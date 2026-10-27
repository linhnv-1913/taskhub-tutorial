import runpy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.core.config import Settings, settings


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "http://a.com/path",
        "ftp://a.com",
        "a.com",
        "https://user:password@a.com",
        "https://a.com?query=value",
        "https://a.com#fragment",
        "",
    ],
)
def test_cors_rejects_invalid_origins(origin):
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, cors_allowed_origins=[origin])
    assert exc.value.errors()[0]["loc"] == ("cors_allowed_origins",)


def test_cors_normalizes_explicit_origins():
    config = Settings(
        _env_file=None,
        cors_allowed_origins=[" http://localhost:3000/ ", "https://a.com"],
    )
    assert config.cors_allowed_origins == ["http://localhost:3000", "https://a.com"]


def test_cors_can_be_disabled_by_omitting_variable_or_using_empty_json(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    assert Settings(_env_file=None).cors_allowed_origins == []
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "[]")
    assert Settings(_env_file=None).cors_allowed_origins == []


@pytest.fixture
def cors_client(monkeypatch):
    monkeypatch.setattr(
        settings, "cors_allowed_origins", ["https://frontend.example.com"]
    )
    # Execute the real application setup with isolated settings and middleware state.
    application = runpy.run_path(main.__file__)["app"]
    with TestClient(application) as client:
        yield client


def test_cors_preflight_allows_configured_origin_and_bearer_headers(cors_client):
    response = cors_client.options(
        "/api/tags",
        headers={
            "Origin": "https://frontend.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://frontend.example.com"
    )
    assert "POST" in response.headers["access-control-allow-methods"].split(", ")
    allowed_headers = (
        response.headers["access-control-allow-headers"].lower().split(", ")
    )
    assert {"authorization", "content-type"} <= set(allowed_headers)
    assert "access-control-allow-credentials" not in response.headers


def test_cors_preflight_rejects_unconfigured_origin(cors_client):
    response = cors_client.options(
        "/api/tags",
        headers={
            "Origin": "https://untrusted.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
