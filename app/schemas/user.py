from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ORMReadModel
from app.schemas.project import ProjectSummary


class UserCreate(ORMReadModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=200)


class UserUpdate(ORMReadModel):
    username: str | None = Field(default=None, min_length=3, max_length=80)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=200)

    @field_validator("username", "email")
    @classmethod
    def required_fields_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("field cannot be null")
        return value


class UserRead(ORMReadModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None


class UserProfile(ORMReadModel):
    id: int
    username: str
    full_name: str | None
    projects: list[ProjectSummary] = Field(default_factory=list)
