from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import SessionDep
from app.crud.exceptions import DuplicateResourceError
from app.crud.tags import create_tag, list_tags
from app.schemas.tag import TagCreate, TagRead

router = APIRouter()


@router.get("", response_model=list[TagRead])
def read_tags(db: SessionDep) -> list[TagRead]:
    return list_tags(db)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag_route(payload: TagCreate, db: SessionDep) -> TagRead:
    try:
        return create_tag(db, payload)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
