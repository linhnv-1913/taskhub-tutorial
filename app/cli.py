"""Operator commands: python -m app.cli create-admin / seed."""

import argparse
import getpass
import logging
import sys

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import constants, messages
from app.core.config import settings
from app.core.enums import UserRole
from app.core.exceptions import ApplicationError, ForbiddenError, ResourceNotFoundError
from app.core.logging_config import configure_logging
from app.crud.users import create_user
from app.db.session import SessionLocal
from app.models import Project, Task, User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


def seed(db: Session, owner_username: str) -> None:
    """Create a small demo project without changing existing records or roles."""
    with db.begin():
        owner = db.scalar(
            select(User).where(User.username == owner_username).with_for_update()
        )
        if owner is None:
            raise ResourceNotFoundError(messages.USER_NOT_FOUND)
        if not owner.is_active:
            raise ForbiddenError(messages.ACCOUNT_INACTIVE)
        project = db.scalar(
            select(Project).where(
                Project.owner_id == owner.id,
                Project.name == constants.DEMO_PROJECT_NAME,
            )
        )
        if project is None:
            project = Project(
                name=constants.DEMO_PROJECT_NAME,
                description=constants.DEMO_PROJECT_DESCRIPTION,
                owner_id=owner.id,
            )
            db.add(project)
            db.flush()
        for title in constants.DEMO_TASK_TITLES:
            existing = db.scalar(
                select(Task.id).where(
                    Task.project_id == project.id, Task.title == title
                )
            )
            if existing is None:
                db.add(Task(title=title, project_id=project.id, assignee_id=owner.id))


def main(argv: list[str] | None = None) -> int:
    configure_logging(settings.log_level)
    parser = argparse.ArgumentParser(description=messages.CLI_DESCRIPTION)
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help=messages.CLI_CREATE_ADMIN_HELP)
    admin.add_argument("--username", required=True)
    admin.add_argument("--email", required=True)
    admin.add_argument("--full-name")
    demo = commands.add_parser("seed", help=messages.CLI_SEED_HELP)
    demo.add_argument("--owner", required=True, help=messages.CLI_OWNER_HELP)
    args = parser.parse_args(argv)

    try:
        if args.command == "create-admin":
            password = getpass.getpass(messages.CLI_PASSWORD_PROMPT)
            if password != getpass.getpass(messages.CLI_PASSWORD_CONFIRM_PROMPT):
                print(messages.CLI_PASSWORD_MISMATCH, file=sys.stderr)
                return 1
            payload = UserCreate(
                username=args.username,
                email=args.email,
                full_name=args.full_name,
                password=password,
            )
            with SessionLocal() as db:
                user = create_user(db, payload, role=UserRole.ADMIN)
                print(
                    messages.CLI_ADMIN_CREATED.format(
                        username=user.username, id=user.id
                    )
                )
        else:
            with SessionLocal() as db:
                seed(db, args.owner)
            print(messages.CLI_DEMO_READY)
    except ValidationError as exc:
        for issue in exc.errors(include_input=False, include_url=False):
            field = ".".join(str(part) for part in issue["loc"])
            print(
                messages.CLI_VALIDATION_ERROR.format(field=field, message=issue["msg"]),
                file=sys.stderr,
            )
        return 1
    except ApplicationError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    except SQLAlchemyError:
        logger.exception(messages.CLI_DATABASE_FAILED)
        print(messages.CLI_DATABASE_FAILED, file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print(messages.CLI_CANCELLED, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
