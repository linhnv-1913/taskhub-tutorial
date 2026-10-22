from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.api.responses import error_responses
from app.crud.tags import create_tag, list_tags
from app.schemas.tag import TagCreate, TagRead

router = APIRouter()


@router.get(
    "",
    response_model=list[TagRead],
    summary="List tags",
    responses=error_responses(status.HTTP_500_INTERNAL_SERVER_ERROR),
)
def read_tags(db: SessionDep) -> list[TagRead]:
    return [TagRead.model_validate(tag) for tag in list_tags(db)]


@router.post(
    "",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag",
    responses=error_responses(
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_tag_route(payload: TagCreate, db: SessionDep) -> TagRead:
    return TagRead.model_validate(create_tag(db, payload))
