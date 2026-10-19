from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.crud.transactions import commit_or_rollback
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def _project_details_statement():
    return select(Project).options(
        joinedload(Project.tasks).selectinload(Task.tags)
    )


def list_projects(db: Session) -> list[Project]:
    statement = select(Project).options(
        selectinload(Project.tasks).selectinload(Task.tags)
    ).order_by(Project.id)
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: int) -> Project | None:
    statement = _project_details_statement().where(Project.id == project_id)
    return db.scalars(statement).unique().one_or_none()


def create_project(db: Session, payload: ProjectCreate) -> Project:
    if db.get(User, payload.owner_id) is None:
        raise LookupError("Project owner not found")
    project = Project(**payload.model_dump())
    db.add(project)
    commit_or_rollback(db)
    db.refresh(project)
    return project


def update_project(
    db: Session, project_id: int, payload: ProjectUpdate
) -> Project | None:
    project = db.get(Project, project_id)
    if project is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    commit_or_rollback(db)
    return get_project(db, project_id)


def delete_project(db: Session, project_id: int) -> bool:
    project = db.get(Project, project_id)
    if project is None:
        return False
    db.delete(project)
    commit_or_rollback(db)
    return True
