from typing import Annotated

from pydantic import EmailStr, Field, StringConstraints

from app.core import constants
from app.schemas.common import BaseSchema, ORMReadModel
from app.schemas.project import ProjectSummary

Password = Annotated[
    str,
    StringConstraints(
        min_length=constants.PASSWORD_MIN_LENGTH,
        max_length=constants.PASSWORD_MAX_LENGTH,
        strip_whitespace=False,
    ),
]


class UserCreate(BaseSchema):
    username: str = Field(
        min_length=constants.USERNAME_MIN_LENGTH,
        max_length=constants.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str | None = Field(
        default=None,
        max_length=constants.USER_FULL_NAME_MAX_LENGTH,
    )
    password: Password


class UserUpdate(BaseSchema):
    username: str = Field(
        min_length=constants.USERNAME_MIN_LENGTH,
        max_length=constants.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(max_length=constants.USER_EMAIL_MAX_LENGTH)
    full_name: str | None = Field(..., max_length=constants.USER_FULL_NAME_MAX_LENGTH)


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
