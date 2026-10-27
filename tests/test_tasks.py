from fastapi.testclient import TestClient

from tests.helpers import create_project_and_task, register_and_login


def test_bookmark_is_user_specific_and_idempotent(client: TestClient) -> None:
    _, owner_headers = register_and_login(client, "bookmark-owner")
    _, other_headers = register_and_login(client, "bookmark-other")
    _, task = create_project_and_task(client, owner_headers, "Bookmarks")
    url = f"/api/tasks/{task['id']}/bookmark"
    assert client.post(url, headers=owner_headers).status_code == 201
    assert client.post(url, headers=owner_headers).status_code == 200
    assert client.delete(url, headers=other_headers).status_code == 404
    assert client.delete(url, headers=owner_headers).status_code == 204
    assert client.delete(url, headers=owner_headers).status_code == 404


def test_task_filters_and_pagination(client: TestClient) -> None:
    _, headers = register_and_login(client, "filter-owner")
    project, _ = create_project_and_task(client, headers, "Task filters")
    url = f"/api/projects/{project['id']}/tasks"
    ids = []
    for title, priority in [("High one", "HIGH"), ("Low", "LOW"), ("High two", "HIGH")]:
        response = client.post(url, headers=headers, json={"title": title, "priority": priority})
        assert response.status_code == 201
        if priority == "HIGH":
            ids.append(response.json()["id"])
    response = client.get(
        "/api/tasks", headers=headers,
        params={"status": "TODO", "priority": "HIGH", "skip": 1, "limit": 1},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["id"] for item in response.json()["items"]] == ids[1:]
    assert client.get("/api/tasks", headers=headers, params={"limit": 0}).status_code == 422
