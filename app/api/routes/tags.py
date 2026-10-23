from fastapi import APIRouter, status

from app.api.dependencies import (
    AdminUserDep,
    CurrentActiveUserDep,
    PaginationDep,
    SessionDep,
)
from app.api.responses import HTTP_422_UNPROCESSABLE_CONTENT, error_responses
from app.crud.tags import create_tag, list_tags
from app.schemas.common import PaginatedResponse
from app.schemas.tag import TagCreate, TagRead

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TagRead],
    summary="List tags",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_tags(
    db: SessionDep,
    pagination: PaginationDep,
    _current_user: CurrentActiveUserDep,
) -> PaginatedResponse[TagRead]:
    tags, total = list_tags(db, pagination)
    return PaginatedResponse[TagRead](
        items=[TagRead.model_validate(tag) for tag in tags], total=total
    )


@router.post(
    "",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_tag_route(
    payload: TagCreate,
    db: SessionDep,
    _admin: AdminUserDep,
) -> TagRead:
    return TagRead.model_validate(create_tag(db, payload))
