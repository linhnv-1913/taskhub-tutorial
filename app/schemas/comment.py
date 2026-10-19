from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import ORMReadModel


class CommentCreate(ORMReadModel):
    content: str = Field(min_length=1)
    task_id: int = Field(gt=0)
    author_id: int = Field(gt=0)


class CommentUpdate(ORMReadModel):
    content: str | None = Field(default=None, min_length=1)

    @field_validator("content")
    @classmethod
    def content_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("content cannot be null")
        return value


class CommentRead(ORMReadModel):
    id: int
    content: str
    task_id: int
    author_id: int
    created_at: datetime
