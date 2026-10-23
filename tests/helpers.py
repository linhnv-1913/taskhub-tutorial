from fastapi.testclient import TestClient

TEST_PASSWORD = "taskhub-test-password"


def register_and_login(
    client: TestClient, username: str
) -> tuple[dict[str, object], dict[str, str]]:
    registration = client.post(
        "/api/users/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "full_name": username.title(),
            "password": TEST_PASSWORD,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/users/login",
        data={"username": username, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return registration.json(), {"Authorization": f"Bearer {token}"}


def create_project_and_task(
    client: TestClient,
    owner_headers: dict[str, str],
    project_name: str,
    assignee_id: int | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    project_response = client.post(
        "/api/projects",
        headers=owner_headers,
        json={"name": project_name},
    )
    assert project_response.status_code == 201
    project = project_response.json()

    task_response = client.post(
        f"/api/projects/{project['id']}/tasks",
        headers=owner_headers,
        json={"title": "Review onboarding flow", "assignee_id": assignee_id},
    )
    assert task_response.status_code == 201
    return project, task_response.json()
