from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import SessionDep
from app.crud.exceptions import DuplicateResourceError
from app.crud.users import create_user, get_user_profile
from app.schemas.user import UserCreate, UserProfile, UserRead

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_route(payload: UserCreate, db: SessionDep) -> UserRead:
    try:
        return create_user(db, payload)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{username}/profile", response_model=UserProfile)
def read_user_profile(username: str, db: SessionDep) -> UserProfile:
    user = get_user_profile(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
