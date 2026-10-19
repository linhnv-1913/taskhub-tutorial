from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import SessionDep
from app.crud.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()


@router.get("", response_model=list[ProjectRead])
def read_projects(db: SessionDep) -> list[ProjectRead]:
    return list_projects(db)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_route(payload: ProjectCreate, db: SessionDep) -> ProjectRead:
    try:
        return create_project(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: int, db: SessionDep) -> ProjectRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_route(
    project_id: int, payload: ProjectUpdate, db: SessionDep
) -> ProjectRead:
    project = update_project(db, project_id, payload)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_route(project_id: int, db: SessionDep) -> Response:
    if not delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
