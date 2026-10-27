import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.crud.comments import update_task_comment
from app.models.comment import Comment
from app.schemas.comment import CommentUpdate
from app.services import comment_notifications
from app.services.comment_notifications import CommentNotification
from tests.helpers import create_project_and_task, register_and_login


def test_comment_update_refreshes_state_after_concurrent_edit(
    client: TestClient, db_session_factory: sessionmaker
) -> None:
    _, headers = register_and_login(client, "concurrent-comment-author")
    _, task = create_project_and_task(client, headers, "Concurrent comment")
    response = client.post(
        f"/api/tasks/{task['id']}/comments", headers=headers, json={"content": "old"}
    )
    assert response.status_code == 201
    comment_id = response.json()["id"]

    with db_session_factory() as first:
        comment = first.get(Comment, comment_id)
        assert comment.content == "old"
        with db_session_factory() as second:
            second.get(Comment, comment_id).content = "new"
            second.commit()
        result = update_task_comment(first, comment, CommentUpdate(content="old"))
        assert result.content == "old"

    with db_session_factory() as verification:
        assert verification.get(Comment, comment_id).content == "old"


@pytest.mark.parametrize("title", ["First\nSecond", "First\rSecond", "First\r\nSecond"])
def test_notification_sends_when_task_title_contains_newlines(monkeypatch, title) -> None:
    sent = []

    class SMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(comment_notifications.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(comment_notifications.settings, "smtp_from_email", "from@example.com")
    monkeypatch.setattr(comment_notifications.settings, "smtp_starttls", False)
    monkeypatch.setattr(comment_notifications.settings, "smtp_username", None)
    monkeypatch.setattr(comment_notifications.settings, "smtp_password", None)
    monkeypatch.setattr(comment_notifications.smtplib, "SMTP", SMTP)

    comment_notifications.send_task_comment_notification(
        CommentNotification("to@example.com", title, "Author", "Comment")
    )

    assert len(sent) == 1
    assert sent[0]["Subject"] == "New comment on task: First Second"
    assert "First\nSecond" in sent[0].get_content()
