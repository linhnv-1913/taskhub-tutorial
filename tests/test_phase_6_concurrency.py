import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.sql.dml import Delete

from app.models.comment import Comment
from app.models.task import Task
from tests.helpers import create_project_and_task, register_and_login


def test_assignment_returns_404_if_task_is_deleted_during_commit(
    client: TestClient,
    db_session_factory: sessionmaker,
    monkeypatch,
) -> None:
    _, owner_headers = register_and_login(client, "race-task-owner")
    assignee, _ = register_and_login(client, "race-task-assignee")
    _, task = create_project_and_task(client, owner_headers, "Assignment race")

    def delete_task_during_commit(db) -> None:
        db.rollback()
        with db_session_factory() as concurrent_db:
            concurrent_task = concurrent_db.get(Task, task["id"])
            assert concurrent_task is not None
            concurrent_db.delete(concurrent_task)
            concurrent_db.commit()
        raise StaleDataError("Task was deleted by a concurrent request")

    monkeypatch.setattr("app.crud.tasks.commit_or_rollback", delete_task_during_commit)
    response = client.post(
        f"/api/tasks/{task['id']}/assign",
        headers=owner_headers,
        json={"assignee_id": assignee["id"]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_comment_mutation_returns_404_if_comment_is_deleted_during_commit(
    client: TestClient,
    db_session_factory: sessionmaker,
    monkeypatch,
    method: str,
) -> None:
    _, owner_headers = register_and_login(client, f"race-comment-owner-{method}")
    _, author_headers = register_and_login(client, f"race-comment-author-{method}")
    _, task = create_project_and_task(client, owner_headers, f"Comment race {method}")
    create_response = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=author_headers,
        json={"content": "Comment to mutate"},
    )
    comment_id = create_response.json()["id"]

    def delete_comment_during_commit(db) -> None:
        db.rollback()
        with db_session_factory() as concurrent_db:
            concurrent_comment = concurrent_db.get(Comment, comment_id)
            assert concurrent_comment is not None
            concurrent_db.delete(concurrent_comment)
            concurrent_db.commit()
        raise StaleDataError("Comment was deleted by a concurrent request")

    monkeypatch.setattr(
        "app.crud.comments.commit_or_rollback",
        delete_comment_during_commit,
    )
    comment_url = f"/api/tasks/{task['id']}/comments/{comment_id}"
    if method == "patch":
        response = client.patch(
            comment_url,
            headers=author_headers,
            json={"content": "Edited comment"},
        )
    else:
        response = client.delete(comment_url, headers=author_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Task comment not found"


def test_comment_delete_returns_404_if_no_row_matches_delete(
    client: TestClient,
    db_session_factory: sessionmaker,
    monkeypatch,
) -> None:
    _, owner_headers = register_and_login(client, "delete-race-owner")
    _, author_headers = register_and_login(client, "delete-race-author")
    _, task = create_project_and_task(client, owner_headers, "Delete statement race")
    created = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=author_headers,
        json={"content": "Comment to delete"},
    )
    comment_id = created.json()["id"]
    original_execute = SQLAlchemySession.execute
    race_triggered = False

    def delete_before_statement(db, statement, *args, **kwargs):
        nonlocal race_triggered
        if (
            not race_triggered
            and isinstance(statement, Delete)
            and statement.table.name == Comment.__tablename__
        ):
            race_triggered = True
            db.rollback()
            with db_session_factory() as concurrent_db:
                concurrent_comment = concurrent_db.get(Comment, comment_id)
                assert concurrent_comment is not None
                concurrent_db.delete(concurrent_comment)
                concurrent_db.commit()
        return original_execute(db, statement, *args, **kwargs)

    monkeypatch.setattr(SQLAlchemySession, "execute", delete_before_statement)
    response = client.delete(
        f"/api/tasks/{task['id']}/comments/{comment_id}",
        headers=author_headers,
    )

    assert race_triggered
    assert response.status_code == 404
    assert response.json()["detail"] == "Task comment not found"
