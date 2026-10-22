from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import messages
from app.core.exceptions import DuplicateResourceError
from app.crud.transactions import commit_or_rollback
from app.models.tag import Tag
from app.schemas.common import PaginationParams
from app.schemas.tag import TagCreate


def list_tags(
    db: Session, pagination: PaginationParams
) -> tuple[list[Tag], int]:
    statement = (
        select(Tag)
        .order_by(Tag.name)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    total = db.scalar(select(func.count(Tag.id))) or 0
    return list(db.scalars(statement).all()), total


def create_tag(db: Session, payload: TagCreate) -> Tag:
    if db.scalar(select(Tag).where(Tag.name == payload.name)) is not None:
        raise DuplicateResourceError(messages.DUPLICATE_TAG)
    tag = Tag(name=payload.name)
    db.add(tag)
    try:
        commit_or_rollback(db)
    except IntegrityError as exc:
        raise DuplicateResourceError(messages.DUPLICATE_TAG) from exc
    db.refresh(tag)
    return tag
