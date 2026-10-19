from pydantic import Field, field_validator

from app.schemas.common import ORMReadModel
from app.schemas.task import TaskRead


class ProjectCreate(ORMReadModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    owner_id: int = Field(gt=0)


class ProjectUpdate(ORMReadModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class ProjectSummary(ORMReadModel):
    id: int
    name: str
    description: str | None
    owner_id: int


class ProjectRead(ProjectSummary):
    tasks: list[TaskRead] = Field(default_factory=list)
