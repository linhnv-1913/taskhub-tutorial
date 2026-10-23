from pydantic import Field, PositiveInt

from app.core import constants
from app.core.enums import TaskPriority, TaskStatus
from app.schemas.common import BaseSchema, ORMReadModel
from app.schemas.tag import TagRead


class TaskCreate(BaseSchema):
    title: str = Field(
        min_length=constants.TASK_TITLE_MIN_LENGTH,
        max_length=constants.TASK_TITLE_MAX_LENGTH,
    )
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: PositiveInt | None = None
    tag_ids: list[PositiveInt] = Field(default_factory=list)


class TaskRead(ORMReadModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    assignee_id: int | None
    tags: list[TagRead]


class BookmarkRead(ORMReadModel):
    task_id: int
    bookmarked: bool
