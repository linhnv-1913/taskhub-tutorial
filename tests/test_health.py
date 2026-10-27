import logging

from sqlalchemy.exc import OperationalError

from app.api.dependencies import get_db
from app.main import app


def test_health_ready(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_failure_returns_503_and_logs_traceback(client, caplog):
    class UnavailableSession:
        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, RuntimeError("database offline"))

    original = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = lambda: UnavailableSession()
    try:
        with caplog.at_level(logging.ERROR, logger="app.api.routes.health"):
            response = client.get("/api/health")
    finally:
        app.dependency_overrides[get_db] = original
    assert response.status_code == 503
    assert response.json() == {"detail": "Service unavailable"}
    assert any(record.exc_info for record in caplog.records)
