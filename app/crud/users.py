from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.crud.exceptions import DuplicateResourceError
from app.crud.transactions import commit_or_rollback
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    existing = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == str(payload.email))
        )
    )
    if existing:
        raise DuplicateResourceError("Username or email already exists")

    user = User(**payload.model_dump())
    db.add(user)
    try:
        commit_or_rollback(db)
    except IntegrityError as exc:
        raise DuplicateResourceError("Username or email already exists") from exc
    db.refresh(user)
    return user


def get_user_profile(db: Session, username: str) -> User | None:
    statement = (
        select(User)
        .where(User.username == username)
        .options(selectinload(User.projects))
    )
    return db.scalar(statement)
