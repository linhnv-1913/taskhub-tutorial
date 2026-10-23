from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentActiveUserDep, SessionDep
from app.api.responses import HTTP_422_UNPROCESSABLE_CONTENT, error_responses
from app.crud.comments import (
    create_task_comment,
    delete_task_comment,
    update_task_comment,
)
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate

router = APIRouter()


@router.post(
    "/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_task_comment_route(
    task_id: int,
    payload: CommentCreate,

    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> CommentRead:
    comment, task = create_task_comment(db, task_id, current_user, payload)
    return CommentRead.model_validate(comment)


@router.patch(
    "/{task_id}/comments/{comment_id}",
    response_model=CommentRead,
    summary="Edit a task comment",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def update_task_comment_route(
    task_id: int,
    comment_id: int,
    payload: CommentUpdate,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> CommentRead:
    comment = update_task_comment(db, task_id, comment_id, current_user, payload)
    return CommentRead.model_validate(comment)


@router.delete(
    "/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task comment",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def delete_task_comment_route(
    task_id: int,
    comment_id: int,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> Response:
    delete_task_comment(db, task_id, comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
