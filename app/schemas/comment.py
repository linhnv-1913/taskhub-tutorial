from datetime import datetime

from pydantic import Field

from app.core import constants
from app.schemas.common import BaseSchema, ORMReadModel


class CommentWrite(BaseSchema):
    content: str = Field(min_length=1, max_length=constants.COMMENT_CONTENT_MAX_LENGTH)


class CommentCreate(CommentWrite):
    pass


class CommentUpdate(CommentWrite):
    pass


class CommentRead(ORMReadModel):
    id: int
    content: str
    task_id: int
    author_id: int
    created_at: datetime
