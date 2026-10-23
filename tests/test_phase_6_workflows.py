from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.enums import UserRole
from app.models.user import User
from tests.helpers import create_project_and_task, register_and_login


def test_assignment_and_comment_permissions(
    client: TestClient,
    db_session_factory: sessionmaker,
) -> None:
    _owner, owner_headers = register_and_login(client, "workflow-owner")
    assignee, _ = register_and_login(client, "workflow-assignee")
    _author, author_headers = register_and_login(client, "comment-author")
    _stranger, stranger_headers = register_and_login(client, "comment-stranger")
    moderator, moderator_headers = register_and_login(client, "comment-moderator")
    administrator, admin_headers = register_and_login(client, "comment-admin")
    _, task = create_project_and_task(
        client, owner_headers, "Workflow project"
    )

    with db_session_factory() as db:
        db.scalar(select(User).where(User.id == moderator["id"])).role = UserRole.PM
        db.scalar(
            select(User).where(User.id == administrator["id"])
        ).role = UserRole.ADMIN
        db.commit()

    task_url = f"/api/tasks/{task['id']}"
    assert client.post(
        f"{task_url}/assign",
        headers=stranger_headers,
        json={"assignee_id": assignee["id"]},
    ).status_code == 403
    assert client.post(
        f"{task_url}/assign",
        headers=moderator_headers,
        json={"assignee_id": assignee["id"]},
    ).status_code == 403
    assert client.post(
        f"{task_url}/assign",
        headers=owner_headers,
        json={"assignee_id": 99999},
    ).status_code == 422
    assigned = client.post(
        f"{task_url}/assign",
        headers=owner_headers,
        json={"assignee_id": assignee["id"]},
    )
    assert assigned.status_code == 200
    assert assigned.json()["assignee_id"] == assignee["id"]

    comment_response = client.post(
        f"{task_url}/comments",
        headers=author_headers,
        json={"content": "A comment from another active user."},
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["id"]
    comment_url = f"{task_url}/comments/{comment_id}"

    assert client.patch(
        comment_url,
        headers=stranger_headers,
        json={"content": "Unauthorized edit"},
    ).status_code == 403
    assert client.patch(
        comment_url,
        headers=author_headers,
        json={"content": "Edited by the author"},
    ).status_code == 200
    assert client.patch(
        comment_url,
        headers=moderator_headers,
        json={"content": "Reviewed by PM"},
    ).status_code == 403
    assert client.delete(comment_url, headers=stranger_headers).status_code == 403
    assert client.delete(comment_url, headers=moderator_headers).status_code == 403
    assert client.delete(comment_url, headers=owner_headers).status_code == 204

    second_comment = client.post(
        f"{task_url}/comments",
        headers=author_headers,
        json={"content": "A second comment."},
    )
    second_comment_url = f"{task_url}/comments/{second_comment.json()['id']}"
    assert client.delete(second_comment_url, headers=admin_headers).status_code == 204


def test_comment_cannot_be_mutated_through_another_task_path(
    client: TestClient,
) -> None:
    _, owner_headers = register_and_login(client, "wrong-path-owner")
    _, author_headers = register_and_login(client, "wrong-path-author")
    _, task = create_project_and_task(client, owner_headers, "Original comment task")
    _, other_task = create_project_and_task(
        client, owner_headers, "Different path task"
    )
    comment = client.post(
        f"/api/tasks/{task['id']}/comments",
        headers=author_headers,
        json={"content": "Bound to the original task"},
    ).json()
    wrong_path = f"/api/tasks/{other_task['id']}/comments/{comment['id']}"

    assert client.patch(
        wrong_path,
        headers=author_headers,
        json={"content": "Wrong task"},
    ).status_code == 404
    assert client.delete(wrong_path, headers=author_headers).status_code == 404
