from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import messages
from app.core.security import hash_password, verify_password
from app.core.exceptions import (
    AuthenticationError,
    DuplicateResourceError,
    ForbiddenError,
)
from app.crud.transactions import commit_or_rollback
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def _ensure_user_available(
    db: Session, username: str, normalized_email: str, user_id: int | None = None
) -> None:
    statement = select(User).where(
        or_(
            User.username == username,
            func.lower(User.email) == normalized_email,
            func.lower(User.username) == normalized_email,
            func.lower(User.email) == username.lower(),
        )
    )
    if user_id is not None:
        statement = statement.where(User.id != user_id)
    if db.scalar(statement) is not None:
        raise DuplicateResourceError(messages.DUPLICATE_USER)


def create_user(db: Session, payload: UserCreate) -> User:
    normalized_email = str(payload.email).lower()
    _ensure_user_available(db, payload.username, normalized_email)
    user = User(
        username=payload.username,
        email=normalized_email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        commit_or_rollback(db)
    except IntegrityError as exc:
        raise DuplicateResourceError(messages.DUPLICATE_USER) from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    identifier = username.strip()
    matches = db.scalars(
        select(User).where(
            or_(
                User.username == identifier,
                func.lower(User.email) == identifier.lower(),
            )
        )
    ).all()
    user = matches[0] if len(matches) == 1 else None
    stored_hash = user.password_hash if user is not None else None
    if not verify_password(password, stored_hash):
        raise AuthenticationError(messages.INVALID_CREDENTIALS)
    if not user.is_active:
        raise ForbiddenError(messages.ACCOUNT_INACTIVE)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    normalized_email = str(payload.email).lower()
    _ensure_user_available(db, payload.username, normalized_email, user.id)
    user.username = payload.username
    user.email = normalized_email
    user.full_name = payload.full_name
    try:
        commit_or_rollback(db)
    except IntegrityError as exc:
        raise DuplicateResourceError(messages.DUPLICATE_USER) from exc
    db.refresh(user)
    return user


def get_user_profile(db: Session, username: str) -> User | None:
    statement = (
        select(User)
        .where(User.username == username)
        .options(selectinload(User.projects))
    )
    return db.scalar(statement)
