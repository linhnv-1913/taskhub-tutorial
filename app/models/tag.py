from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.task_tags import task_tags

if TYPE_CHECKING:
    from app.models.task import Task


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    tasks: Mapped[list["Task"]] = relationship(
        secondary=task_tags, back_populates="tags"
    )
