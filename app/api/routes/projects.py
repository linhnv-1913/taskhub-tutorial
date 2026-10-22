from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentActiveUserDep, ProjectManagerDep, SessionDep
from app.api.responses import error_responses
from app.core import messages
from app.core.exceptions import ResourceNotFoundError
from app.crud.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[ProjectSummary],
    summary="List projects",
    responses=error_responses(status.HTTP_500_INTERNAL_SERVER_ERROR),
)
def read_projects(db: SessionDep) -> list[ProjectSummary]:
    return [ProjectSummary.model_validate(project) for project in list_projects(db)]


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_project_route(
    payload: ProjectCreate,
    db: SessionDep,
    current_user: CurrentActiveUserDep,
) -> ProjectRead:
    return ProjectRead.model_validate(create_project(db, payload, current_user.id))


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project details",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_project(project_id: int, db: SessionDep) -> ProjectRead:
    project = get_project(db, project_id)
    if project is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    return ProjectRead.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def update_project_route(
    project_id: int,
    payload: ProjectUpdate,
    db: SessionDep,
    _manager: ProjectManagerDep,
) -> ProjectRead:
    project = update_project(db, project_id, payload)
    if project is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def delete_project_route(
    project_id: int,
    db: SessionDep,
    _manager: ProjectManagerDep,
) -> Response:
    if not delete_project(db, project_id):
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
