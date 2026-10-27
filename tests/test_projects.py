from fastapi.testclient import TestClient

from tests.helpers import create_project_and_task, register_and_login


def test_project_mutation_requires_owner_or_admin(client: TestClient) -> None:
    _, owner_headers = register_and_login(client, "project-owner")
    _, outsider_headers = register_and_login(client, "project-outsider")
    project, _ = create_project_and_task(client, owner_headers, "Restricted project")
    url = f"/api/projects/{project['id']}"
    assert client.patch(url, headers=outsider_headers, json={"name": "Forbidden"}).status_code == 403
    assert client.delete(url, headers=outsider_headers).status_code == 403
    assert client.patch(url, headers=owner_headers, json={"name": "Updated"}).status_code == 200
