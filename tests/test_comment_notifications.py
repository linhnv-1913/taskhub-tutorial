import logging
import warnings

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.api.router import api_router
from app.models.comment import Comment
from app.models.user import User
from app.services import comment_notifications
from app.services.comment_notifications import CommentNotification
from tests.helpers import create_project_and_task, register_and_login


def test_registration_and_authenticated_task_creation(client: TestClient) -> None:
    user, headers = register_and_login(client, "task-creator")
    project, task = create_project_and_task(
        client, headers, "Registration integration project"
    )

    assert user["id"] > 0
    assert task["project_id"] == project["id"]
    assert task["status"] == "TODO"
    assert task["assignee_id"] is None


def test_comment_queues_email_after_commit(
    client: TestClient,
    db_session_factory: sessionmaker,
    monkeypatch,
) -> None:
    _, owner_headers = register_and_login(client, "task-owner")
    assignee, _ = register_and_login(client, "task-assignee")
    commenter, commenter_headers = register_and_login(client, "task-commenter")
    _, task = create_project_and_task(
        client,
        owner_headers,
        "Comment notification project",
        int(assignee["id"]),
    )
    queued: list[CommentNotification] = []

    def record_notification(notification: CommentNotification) -> None:
        with db_session_factory() as db:
            saved_comment = db.scalar(
                select(Comment).where(Comment.task_id == task["id"])
            )
            assert saved_comment is not None
        queued.append(notification)

    monkeypatch.setattr(
        "app.services.comments.send_task_comment_notification",
        record_notification,
    )
    response = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=commenter_headers,
        json={"content": "Please review the updated flow."},
    )

    assert response.status_code == 201
    assert response.json()["author_id"] == commenter["id"]
    assert len(queued) == 1
    assert queued[0].recipient_email == assignee["email"]
    assert queued[0].task_title == task["title"]
    assert queued[0].commenter_name == commenter["full_name"]


def test_unassigned_comment_notifies_owner_but_omits_owner_authored_comment(
    client: TestClient,
    monkeypatch,
) -> None:
    owner, owner_headers = register_and_login(client, "fallback-task-owner")
    _, commenter_headers = register_and_login(client, "fallback-commenter")
    _, task = create_project_and_task(
        client,
        owner_headers,
        "Unassigned notification project",
    )
    queued: list[CommentNotification] = []
    monkeypatch.setattr(
        "app.services.comments.send_task_comment_notification",
        queued.append,
    )

    other_comment = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=commenter_headers,
        json={"content": "Notify the project owner"},
    )
    owner_comment = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=owner_headers,
        json={"content": "The owner wrote this comment"},
    )

    assert other_comment.status_code == 201
    assert owner_comment.status_code == 201
    assert len(queued) == 1
    assert queued[0].recipient_email == owner["email"]


def test_comment_notification_uses_username_when_full_name_missing(
    client: TestClient, db_session_factory: sessionmaker, monkeypatch
) -> None:
    _, owner_headers = register_and_login(client, "notification-owner")
    author, author_headers = register_and_login(client, "notification-author")
    _, task = create_project_and_task(client, owner_headers, "Username fallback")
    with db_session_factory() as db:
        db.get(User, author["id"]).full_name = None
        db.commit()
    sent = []
    monkeypatch.setattr("app.services.comments.send_task_comment_notification", sent.append)
    response = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=author_headers,
        json={"content": "Hello"},
    )
    assert response.status_code == 201
    assert len(sent) == 1
    assert sent[0].commenter_name == author["username"]


def test_smtp_failure_is_logged_without_raising(monkeypatch, caplog) -> None:
    monkeypatch.setattr(comment_notifications.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(
        comment_notifications.settings,
        "smtp_from_email",
        "taskhub@example.com",
    )

    def unavailable_smtp(*_args, **_kwargs):
        raise OSError("SMTP unavailable")

    monkeypatch.setattr(comment_notifications.smtplib, "SMTP", unavailable_smtp)
    notification = CommentNotification(
        recipient_email="assignee@example.com",
        task_title="Task",
        commenter_name="Commenter",
        comment_content="A comment",
    )

    with caplog.at_level(logging.ERROR):
        comment_notifications.send_task_comment_notification(notification)

    assert "Task comment email delivery failed" in caplog.text


def test_api_routes_have_unique_operation_ids() -> None:
    application = FastAPI()
    application.include_router(api_router)

    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="Duplicate Operation ID")
        schema = application.openapi()

    assert "post" in schema["paths"]["/api/tasks/{task_id}/assign"]
    assert "post" in schema["paths"]["/api/tasks/{task_id}/comments"]
