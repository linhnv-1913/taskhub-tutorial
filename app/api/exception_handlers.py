from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core import messages
from app.core.exceptions import ApplicationError
from app.schemas.common import ErrorResponse, ValidationIssue


async def handle_application_error(
    _request: Request, error: ApplicationError
) -> JSONResponse:
    response = ErrorResponse(detail=error.message)
    return JSONResponse(
        status_code=int(error.status_code),
        content=response.model_dump(mode="json", exclude_none=True),
        headers=error.headers,
    )


async def handle_request_validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    issues = [
        ValidationIssue(
            field=".".join(str(part) for part in item["loc"]),
            message=item["msg"],
            type=item["type"],
        )
        for item in error.errors()
    ]
    response = ErrorResponse(
        detail=messages.REQUEST_VALIDATION_FAILED,
        errors=issues,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode="json", exclude_none=True),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, handle_application_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
