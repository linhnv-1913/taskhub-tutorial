from pydantic import BaseModel, ConfigDict


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
