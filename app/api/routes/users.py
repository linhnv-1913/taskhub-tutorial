from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentActiveUserDep, SessionDep
from app.api.responses import error_responses
from app.core import messages
from app.core.exceptions import ResourceNotFoundError
from app.core.security import create_access_token
from app.crud.users import authenticate_user, create_user, get_user_profile, update_user
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserProfile, UserRead, UserUpdate

router = APIRouter()


@router.post(
    "",
    include_in_schema=False,
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    responses=error_responses(
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def register_user_route(payload: UserCreate, db: SessionDep) -> UserRead:
    return UserRead.model_validate(create_user(db, payload))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with a username or email and password",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def login_user(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    return TokenResponse(access_token=create_access_token(user.id))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the authenticated user's account",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_current_user(current_user: CurrentActiveUserDep) -> UserRead:
    return UserRead.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserRead,
    summary="Replace the authenticated user's profile fields",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def update_current_user(
    payload: UserUpdate,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> UserRead:
    return UserRead.model_validate(update_user(db, current_user, payload))


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
