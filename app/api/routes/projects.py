from fastapi import APIRouter, Response, status

from app.api.dependencies import (
    CurrentActiveUserDep,
    PaginationDep,
    ProjectManagerDep,
    SessionDep,
)
from app.api.responses import HTTP_422_UNPROCESSABLE_CONTENT, error_responses
from app.core import messages
from app.core.exceptions import ResourceNotFoundError
from app.crud.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ProjectSummary],
    summary="List projects",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_projects(
    db: SessionDep,
    pagination: PaginationDep,
    _current_user: CurrentActiveUserDep,
) -> PaginatedResponse[ProjectSummary]:
    projects, total = list_projects(db, pagination)
    return PaginatedResponse[ProjectSummary](
        items=[ProjectSummary.model_validate(project) for project in projects],
        total=total,
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def create_project_route(
    payload: ProjectCreate,
    db: SessionDep,
    current_user: CurrentActiveUserDep,
) -> ProjectRead:
    return ProjectRead.model_validate(create_project(db, payload, current_user))


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project details",
    responses=error_responses(
        status.HTTP_404_NOT_FOUND,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def read_project(
    project_id: int,
    db: SessionDep,
    _current_user: CurrentActiveUserDep,
) -> ProjectRead:
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
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def update_project_route(
    payload: ProjectUpdate,
    db: SessionDep,
    project: ProjectManagerDep,
) -> ProjectRead:
    return ProjectRead.model_validate(update_project(db, project, payload))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def delete_project_route(
    db: SessionDep,
    project: ProjectManagerDep,
) -> Response:
    delete_project(db, project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
