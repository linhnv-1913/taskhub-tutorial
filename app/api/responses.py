from http import HTTPStatus

from fastapi import status

from app.schemas.common import ErrorResponse

HTTP_422_UNPROCESSABLE_CONTENT = getattr(
    status, "HTTP_422_UNPROCESSABLE_CONTENT", HTTPStatus.UNPROCESSABLE_ENTITY
)

_ERROR_DESCRIPTIONS = {
    status.HTTP_401_UNAUTHORIZED: "The bearer token or credentials are invalid.",
    status.HTTP_403_FORBIDDEN: "The authenticated user is not allowed to perform this action.",
    status.HTTP_404_NOT_FOUND: "The requested resource was not found.",
    status.HTTP_409_CONFLICT: "The request conflicts with an existing resource.",
    HTTP_422_UNPROCESSABLE_CONTENT: "The request data is invalid.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "An unexpected server error occurred.",
}


def error_responses(*status_codes: int) -> dict[int, dict[str, object]]:
    responses: dict[int, dict[str, object]] = {}
    for code in status_codes:
        response: dict[str, object] = {
            "description": _ERROR_DESCRIPTIONS[code],
        }
        if code != status.HTTP_500_INTERNAL_SERVER_ERROR:
            response["model"] = ErrorResponse
        responses[code] = response
    return responses
