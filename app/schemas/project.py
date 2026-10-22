from pydantic import Field, PositiveInt, field_validator

from app.core import constants, messages
from app.schemas.common import BaseSchema, ORMReadModel
from app.schemas.task import TaskRead


class ProjectCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=constants.PROJECT_NAME_MAX_LENGTH)
    description: str | None = None
    owner_id: PositiveInt


class ProjectUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=constants.PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(messages.PROJECT_NAME_CANNOT_BE_NULL)
        return value


class ProjectSummary(ORMReadModel):
    id: int
    name: str
    description: str | None
    owner_id: int


class ProjectRead(ProjectSummary):
    tasks: list[TaskRead] = Field(default_factory=list)
