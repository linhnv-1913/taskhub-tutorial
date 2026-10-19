from pydantic import Field, field_validator

from app.schemas.common import ORMReadModel


class TagCreate(ORMReadModel):
    name: str = Field(min_length=1, max_length=80)


class TagUpdate(ORMReadModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class TagRead(ORMReadModel):
    id: int
    name: str
