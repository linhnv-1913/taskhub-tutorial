from fastapi import status

from app.schemas.common import ErrorResponse

_ERROR_DESCRIPTIONS = {
    status.HTTP_404_NOT_FOUND: "The requested resource was not found.",
    status.HTTP_409_CONFLICT: "The request conflicts with an existing resource.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "The request data is invalid.",
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
