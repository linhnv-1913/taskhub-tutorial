from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import SessionDep
from app.crud.exceptions import InvalidResourceReferenceError
from app.crud.tasks import create_project_task, list_project_tasks
from app.schemas.task import TaskCreate, TaskRead

router = APIRouter()


@router.get("", response_model=list[TaskRead])
def read_project_tasks(project_id: int, db: SessionDep) -> list[TaskRead]:
    try:
        return list_project_tasks(db, project_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_project_task_route(
    project_id: int, payload: TaskCreate, db: SessionDep
) -> TaskRead:
    try:
        return create_project_task(db, project_id, payload)
    except InvalidResourceReferenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
