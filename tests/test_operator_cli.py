import logging
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app import cli
from app.core import messages
from app.core.enums import UserRole
from app.core.security import verify_password
from app.models import Project, Task, User


def run_admin(
    factory, password="admin-password-123", confirmation=None, username="admin"
):
    with (
        patch.object(cli, "SessionLocal", factory),
        patch.object(
            cli.getpass,
            "getpass",
            side_effect=[password, password if confirmation is None else confirmation],
        ),
    ):
        return cli.main(
            [
                "create-admin",
                "--username",
                username,
                "--email",
                f"{username}@example.com",
            ]
        )


def test_admin_can_log_in_and_duplicates_do_not_overwrite(
    db_session_factory,
    client,
    capsys,
):
    assert run_admin(db_session_factory) == 0
    with db_session_factory() as db:
        user = db.scalar(select(User))
        assert user.role == UserRole.ADMIN
        assert user.is_active
        original_hash = user.password_hash
        assert verify_password("admin-password-123", original_hash)

    login = client.post(
        "/api/users/login",
        data={
            "username": "admin",
            "password": "admin-password-123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert (
        client.post(
            "/api/tags",
            json={"name": "cli-admin"},
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 201
    )

    assert run_admin(db_session_factory, "different-password-123") == 1
    assert "Username or email already exists" in capsys.readouterr().err
    with db_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
        assert db.scalar(select(User.password_hash)) == original_hash


@pytest.mark.parametrize(
    ("username", "password", "confirmation", "expected_error"),
    [
        (
            "short-password",
            "tiny",
            None,
            "password: String should have at least 12 characters",
        ),
        (
            "long-password",
            "x" * 129,
            None,
            "password: String should have at most 128 characters",
        ),
        (
            "mismatched-password",
            "admin-password-123",
            "mismatch",
            "Passwords do not match.",
        ),
    ],
)
def test_admin_password_validation_does_not_write_or_echo_secrets(
    db_session_factory,
    capsys,
    username,
    password,
    confirmation,
    expected_error,
):
    assert run_admin(db_session_factory, "short-secret") == 0  # 12 characters
    capsys.readouterr()
    assert (
        run_admin(
            db_session_factory,
            password,
            confirmation=confirmation,
            username=username,
        )
        == 1
    )
    output = capsys.readouterr()
    assert expected_error in output.err
    assert password not in output.out + output.err
    if confirmation is not None:
        assert confirmation not in output.out + output.err
    with db_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
        assert db.scalar(select(User.username)) == "admin"


@pytest.mark.parametrize("command", ["create-admin", "seed"])
def test_database_failure_returns_failure_and_logs_traceback(command, caplog, capsys):
    error = OperationalError("SELECT 1", {}, RuntimeError("database offline"))
    with (
        patch.object(cli, "SessionLocal", side_effect=error) as factory,
        caplog.at_level(logging.ERROR, logger=cli.__name__),
    ):
        if command == "create-admin":
            result = run_admin(factory)
        else:
            result = cli.main(["seed", "--owner", "admin"])
    assert result == 1
    assert messages.CLI_DATABASE_FAILED in capsys.readouterr().err
    assert any(
        record.name == cli.__name__
        and record.getMessage() == messages.CLI_DATABASE_FAILED
        and record.exc_info is not None
        and record.exc_info[1] is error
        for record in caplog.records
    )


def test_seed_is_repeatable_and_preserves_edits(db_session_factory):
    assert run_admin(db_session_factory) == 0
    with patch.object(cli, "SessionLocal", db_session_factory):
        assert cli.main(["seed", "--owner", "missing"]) == 1
        assert cli.main(["seed", "--owner", "admin"]) == 0
        with db_session_factory.begin() as db:
            task = db.scalar(select(Task).order_by(Task.id))
            task.description = "Keep this edit"
        assert cli.main(["seed", "--owner", "admin"]) == 0
    with db_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Project)) == 1
        assert db.scalar(select(func.count()).select_from(Task)) == 2
        assert db.scalar(select(Task).order_by(Task.id)).description == "Keep this edit"
        assert db.scalar(select(User.role)) == UserRole.ADMIN


def test_seed_rejects_inactive_owner(db_session_factory):
    assert run_admin(db_session_factory) == 0
    with db_session_factory.begin() as db:
        db.scalar(select(User)).is_active = False
    with patch.object(cli, "SessionLocal", db_session_factory):
        assert cli.main(["seed", "--owner", "admin"]) == 1
    with db_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Project)) == 0
