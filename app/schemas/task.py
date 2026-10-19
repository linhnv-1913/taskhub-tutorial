from pydantic import Field, field_validator

from app.schemas.common import ORMReadModel
from app.schemas.tag import TagRead


class TaskCreate(ORMReadModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: str = Field(default="TODO", min_length=1, max_length=32)
    assignee_id: int | None = Field(default=None, gt=0)
    tag_ids: list[int] = Field(default_factory=list)


class TaskUpdate(ORMReadModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    assignee_id: int | None = Field(default=None, gt=0)
    tag_ids: list[int] | None = None

    @field_validator("title", "status")
    @classmethod
    def required_fields_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("tag_ids")
    @classmethod
    def tag_ids_cannot_be_null(cls, value: list[int] | None) -> list[int]:
        if value is None:
            raise ValueError("tag_ids cannot be null")
        return value


class TaskRead(ORMReadModel):
    id: int
    title: str
    description: str | None
    status: str
    project_id: int
    assignee_id: int | None
    tags: list[TagRead]
