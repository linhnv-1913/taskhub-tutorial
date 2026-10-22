from pydantic import Field, PositiveInt

from app.core import constants
from app.core.enums import TaskStatus
from app.schemas.common import BaseSchema, ORMReadModel
from app.schemas.tag import TagRead


class TaskCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=constants.TASK_TITLE_MAX_LENGTH)
    description: str | None = None
    assignee_id: PositiveInt | None = None
    tag_ids: list[PositiveInt] = Field(default_factory=list)


class TaskRead(ORMReadModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    project_id: int
    assignee_id: int | None
    tags: list[TagRead]
