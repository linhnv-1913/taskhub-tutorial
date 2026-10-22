from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import (
    CurrentActiveUserDep,
    PaginationDep,
    ProjectManagerDep,
    SessionDep,
)
from app.api.responses import HTTP_422_UNPROCESSABLE_CONTENT, error_responses
from app.core.enums import TaskPriority, TaskStatus
from app.crud.tasks import (
    bookmark_task,
    create_project_task,
    list_project_tasks,
    list_tasks,
    unbookmark_task,
)
from app.schemas.common import PaginatedResponse
from app.schemas.task import BookmarkRead, TaskCreate, TaskRead

router = APIRouter()
collection_router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
    summary="List tasks in a project",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_project_tasks(
    project_id: int,
    db: SessionDep,
    pagination: PaginationDep,
    _current_user: CurrentActiveUserDep,
) -> PaginatedResponse[TaskRead]:
    tasks, total = list_project_tasks(db, project_id, pagination)
    return PaginatedResponse[TaskRead](
        items=[TaskRead.model_validate(task) for task in tasks], total=total
    )


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_project_task_route(
    payload: TaskCreate,
    db: SessionDep,
    project: ProjectManagerDep,
) -> TaskRead:
    return TaskRead.model_validate(create_project_task(db, project, payload))


@collection_router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
    summary="List tasks with optional status and priority filters",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_tasks(
    db: SessionDep,
    pagination: PaginationDep,
    _current_user: CurrentActiveUserDep,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority_filter: Annotated[TaskPriority | None, Query(alias="priority")] = None,
) -> PaginatedResponse[TaskRead]:
    tasks, total = list_tasks(db, status_filter, priority_filter, pagination)
    return PaginatedResponse[TaskRead](
        items=[TaskRead.model_validate(task) for task in tasks], total=total
    )


@collection_router.post(
    "/{task_id}/bookmark",
    response_model=BookmarkRead,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a task for the authenticated user",
    responses={
        **error_responses(
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
        status.HTTP_200_OK: {
            "description": "The task was already bookmarked.",
            "model": BookmarkRead,
        },
    },
)
def create_task_bookmark(
    task_id: int,
    response: Response,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> BookmarkRead:
    created = bookmark_task(db, current_user.id, task_id)
    if not created:
        response.status_code = status.HTTP_200_OK
    return BookmarkRead(task_id=task_id, bookmarked=True)


@collection_router.delete(
    "/{task_id}/bookmark",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove the authenticated user's task bookmark",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def delete_task_bookmark(
    task_id: int,
    current_user: CurrentActiveUserDep,
    db: SessionDep,
) -> Response:
    unbookmark_task(db, current_user.id, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
