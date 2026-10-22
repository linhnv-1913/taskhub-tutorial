from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.api.responses import error_responses
from app.core import messages
from app.core.exceptions import ResourceNotFoundError
from app.crud.users import create_user, get_user_profile
from app.schemas.user import UserCreate, UserProfile, UserRead

router = APIRouter()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    responses=error_responses(
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_user_route(payload: UserCreate, db: SessionDep) -> UserRead:
    return UserRead.model_validate(create_user(db, payload))


@router.get(
    "/{username}/profile",
    response_model=UserProfile,
    summary="Get a user profile",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_user_profile(username: str, db: SessionDep) -> UserProfile:
    user = get_user_profile(db, username)
    if user is None:
        raise ResourceNotFoundError(messages.USER_NOT_FOUND)
    return UserProfile.model_validate(user)
