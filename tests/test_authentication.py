from fastapi.testclient import TestClient

from tests.helpers import register_and_login


def test_authentication_rejects_bad_credentials_and_missing_token(client: TestClient) -> None:
    register_and_login(client, "auth-user")
    login = client.post(
        "/api/users/login", data={"username": "auth-user", "password": "wrong-password"}
    )
    assert login.status_code == 401
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
