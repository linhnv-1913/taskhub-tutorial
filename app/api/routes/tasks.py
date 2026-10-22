from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.api.responses import error_responses
from app.crud.tasks import create_project_task, list_project_tasks
from app.schemas.task import TaskCreate, TaskRead

router = APIRouter()


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
def read_project_tasks(project_id: int, db: SessionDep) -> list[TaskRead]:
    return [
        TaskRead.model_validate(task)
        for task in list_project_tasks(db, project_id)
    ]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_project_task_route(
    project_id: int, payload: TaskCreate, db: SessionDep
) -> TaskRead:
    return TaskRead.model_validate(create_project_task(db, project_id, payload))
