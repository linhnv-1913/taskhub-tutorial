from http import HTTPStatus


class ApplicationError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    headers: dict[str, str] = {}

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND


class DuplicateResourceError(ApplicationError):
    status_code = HTTPStatus.CONFLICT


class InvalidResourceReferenceError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class AuthenticationError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN


class ServiceUnavailableError(ApplicationError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
