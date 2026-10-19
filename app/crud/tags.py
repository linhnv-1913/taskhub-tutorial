from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.exceptions import DuplicateResourceError
from app.crud.transactions import commit_or_rollback
from app.models.tag import Tag
from app.schemas.tag import TagCreate


def list_tags(db: Session) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.name)).all())


def create_tag(db: Session, payload: TagCreate) -> Tag:
    if db.scalar(select(Tag).where(Tag.name == payload.name)) is not None:
        raise DuplicateResourceError("Tag name already exists")
    tag = Tag(name=payload.name)
    db.add(tag)
    try:
        commit_or_rollback(db)
    except IntegrityError as exc:
        raise DuplicateResourceError("Tag name already exists") from exc
    db.refresh(tag)
    return tag
