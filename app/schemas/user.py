from pydantic import EmailStr, Field

from app.core import constants
from app.schemas.common import BaseSchema, ORMReadModel
from app.schemas.project import ProjectSummary


class UserCreate(BaseSchema):
    username: str = Field(
        min_length=3,
        max_length=constants.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str | None = Field(
        default=None,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )


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
