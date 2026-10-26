from fastapi import APIRouter, Response, status

from app.api.dependencies import (
    CommentOwnerDep,
    CurrentActiveUserDep,
    PaginationDep,
    SessionDep,
)
from app.api.responses import HTTP_422_UNPROCESSABLE_CONTENT, error_responses
from app.crud.comments import (
    create_task_comment,
    delete_task_comment,
    list_task_comments,
    update_task_comment,
)
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get(
    "/{task_id}/comments",
    response_model=PaginatedResponse[CommentRead],
    summary="List comments on a task",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_task_comments(
    task_id: int,
    db: SessionDep,
    pagination: PaginationDep,
    _current_user: CurrentActiveUserDep,
) -> PaginatedResponse[CommentRead]:
    comments, total = list_task_comments(db, task_id, pagination)
    return PaginatedResponse[CommentRead](
        items=[CommentRead.model_validate(comment) for comment in comments],
        total=total,
    )


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
    comment, _task = create_task_comment(db, task_id, current_user, payload)
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
    comment: CommentOwnerDep,
    db: SessionDep,
) -> CommentRead:
    updated_comment = update_task_comment(db, comment, payload)
    return CommentRead.model_validate(updated_comment)


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
    comment: CommentOwnerDep,
    db: SessionDep,
) -> Response:
    delete_task_comment(db, comment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
