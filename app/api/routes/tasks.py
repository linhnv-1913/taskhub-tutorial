from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentActiveUserDep, ProjectManagerDep, SessionDep
from app.api.responses import error_responses
from app.core import constants
from app.core.enums import TaskPriority, TaskStatus
from app.crud.tasks import bookmark_task, create_project_task, list_project_tasks, list_tasks
from app.schemas.task import BookmarkRead, TaskCreate, TaskRead

router = APIRouter()
collection_router = APIRouter()


@router.get(
    "",
    response_model=list[TaskRead],
    summary="List tasks in a project",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_project_tasks(
    project_id: int,
    db: SessionDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(
        default=constants.DEFAULT_PAGE_SIZE,
        ge=1,
        le=constants.MAX_PAGE_SIZE,
    ),
) -> list[TaskRead]:
    return [
        TaskRead.model_validate(task)
        for task in list_project_tasks(db, project_id, skip, limit)
    ]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_project_task_route(
    project_id: int,
    payload: TaskCreate,
    db: SessionDep,
    _manager: ProjectManagerDep,
) -> TaskRead:
    return TaskRead.model_validate(create_project_task(db, project_id, payload))


@collection_router.get(
    "",
    response_model=list[TaskRead],
    summary="List tasks with optional status and priority filters",
    responses=error_responses(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_tasks(
    db: SessionDep,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority_filter: TaskPriority | None = Query(default=None, alias="priority"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(
        default=constants.DEFAULT_PAGE_SIZE,
        ge=1,
        le=constants.MAX_PAGE_SIZE,
    ),
) -> list[TaskRead]:
    return [
        TaskRead.model_validate(task)
        for task in list_tasks(db, status_filter, priority_filter, skip, limit)
    ]


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
            status.HTTP_422_UNPROCESSABLE_ENTITY,
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
