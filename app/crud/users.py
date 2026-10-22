from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import messages
from app.core.exceptions import DuplicateResourceError
from app.crud.transactions import commit_or_rollback
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    normalized_email = str(payload.email).lower()
    existing = db.scalar(
        select(User).where(
            or_(
                User.username == payload.username,
                func.lower(User.email) == normalized_email,
            )
        )
    )
    if existing:
        raise DuplicateResourceError(messages.DUPLICATE_USER)

    user_data = payload.model_dump()
    user_data["email"] = normalized_email
    user = User(**user_data)
    db.add(user)
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
