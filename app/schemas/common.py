from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

PageItem = TypeVar("PageItem")


@dataclass(frozen=True)
class PaginationParams:
    skip: int
    limit: int


class BaseSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ORMReadModel(BaseSchema):
    model_config = ConfigDict(from_attributes=True)


class ValidationIssue(BaseSchema):
    field: str
    message: str
    type: str


class ErrorResponse(BaseSchema):
    detail: str
    errors: list[ValidationIssue] | None = None


class PaginatedResponse(BaseSchema, Generic[PageItem]):
    items: list[PageItem]
    total: int = Field(ge=0)
