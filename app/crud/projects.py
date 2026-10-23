from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.crud.transactions import commit_or_rollback
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.common import PaginationParams
from app.schemas.project import ProjectCreate, ProjectUpdate


def _project_details_statement():
    return select(Project).options(
        selectinload(Project.tasks).selectinload(Task.tags)
    )


def list_projects(
    db: Session, pagination: PaginationParams
) -> tuple[list[Project], int]:
    statement = (
        select(Project)
        .order_by(Project.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    total = db.scalar(select(func.count()).select_from(Project)) or 0
    return list(db.scalars(statement).all()), total


def get_project(db: Session, project_id: int) -> Project | None:
    statement = _project_details_statement().where(Project.id == project_id)
    return db.scalars(statement).one_or_none()


def create_project(db: Session, payload: ProjectCreate, owner: User) -> Project:
    project = Project(**payload.model_dump(), owner=owner)
    db.add(project)
    commit_or_rollback(db)
    db.refresh(project)
    return project


def update_project(
    db: Session, project: Project, payload: ProjectUpdate
) -> Project:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    commit_or_rollback(db)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    commit_or_rollback(db)
