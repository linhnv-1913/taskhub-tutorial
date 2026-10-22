from pydantic import Field

from app.core import constants
from app.schemas.common import BaseSchema, ORMReadModel


class TagCreate(BaseSchema):
    name: str = Field(
        min_length=constants.TAG_NAME_MIN_LENGTH,
        max_length=constants.TAG_NAME_MAX_LENGTH,
    )


class TagRead(ORMReadModel):
    id: int
    name: str
