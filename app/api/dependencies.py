from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import messages
from app.core.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User

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
        raise AuthenticationError(messages.INVALID_CREDENTIALS)
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise ForbiddenError(messages.ACCOUNT_INACTIVE)
    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]


def verify_admin_role(current_user: CurrentActiveUserDep) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(messages.ADMIN_REQUIRED)
    return current_user


AdminUserDep = Annotated[User, Depends(verify_admin_role)]


def verify_project_manager(
    project_id: int,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> User:
    owner_id = db.scalar(select(Project.owner_id).where(Project.id == project_id))
    if owner_id is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    if current_user.role != UserRole.ADMIN and owner_id != current_user.id:
        raise ForbiddenError(messages.PROJECT_MANAGER_REQUIRED)
    return current_user


ProjectManagerDep = Annotated[User, Depends(verify_project_manager)]
