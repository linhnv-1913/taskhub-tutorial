from http import HTTPStatus


class ApplicationError(Exception):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND


class DuplicateResourceError(ApplicationError):
    status_code = HTTPStatus.CONFLICT


class InvalidResourceReferenceError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
