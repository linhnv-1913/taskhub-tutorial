from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import constants, messages
from app.core.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from app.core.security import decode_access_token
from app.crud.projects import get_project
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginationParams
from app.models.task import Task

SessionDep = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/login",
    auto_error=False,
)
TokenDep = Annotated[str | None, Depends(oauth2_scheme)]


def get_current_user(token: TokenDep, db: SessionDep) -> User:
    user_id = decode_access_token(token) if token is not None else None
    user = db.scalar(select(User).where(User.id == user_id)) if user_id else None
    if user is None:
        raise AuthenticationError(messages.CREDENTIALS_COULD_NOT_BE_VALIDATED)
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise ForbiddenError(messages.ACCOUNT_INACTIVE)
    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]


def get_pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=constants.MAX_PAGE_SIZE)
    ] = constants.DEFAULT_PAGE_SIZE,
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]


def verify_admin_role(current_user: CurrentActiveUserDep) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(messages.ADMIN_REQUIRED)
    return current_user


AdminUserDep = Annotated[User, Depends(verify_admin_role)]


def verify_project_manager(
    project_id: int,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> Project:
    project = get_project(db, project_id)
    if project is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    if (
        current_user.role != UserRole.ADMIN
        and project.owner_id != current_user.id
    ):
        raise ForbiddenError(messages.PROJECT_MANAGER_REQUIRED)
    return project


ProjectManagerDep = Annotated[Project, Depends(verify_project_manager)]


def verify_task_project_manager(
    task_id: int,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id).with_for_update())
    if task is None:
        raise ResourceNotFoundError(messages.TASK_NOT_FOUND)
    if (
        current_user.role != UserRole.ADMIN
        and task.project.owner_id != current_user.id
    ):
        raise ForbiddenError(messages.PROJECT_MANAGER_REQUIRED)
    return task


TaskProjectManagerDep = Annotated[
    Task, Depends(verify_task_project_manager)
]
