from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import messages
from app.core.exceptions import (
    InvalidResourceReferenceError,
    ResourceNotFoundError,
)
from app.crud.transactions import commit_or_rollback
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate


def list_project_tasks(db: Session, project_id: int) -> list[Task]:
    if db.get(Project, project_id) is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    statement = (
        select(Task)
        .where(Task.project_id == project_id)
        .options(selectinload(Task.tags))
        .order_by(Task.id)
    )
    return list(db.scalars(statement).all())


def create_project_task(db: Session, project_id: int, payload: TaskCreate) -> Task:
    if db.get(Project, project_id) is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    if payload.assignee_id is not None and db.get(User, payload.assignee_id) is None:
        raise InvalidResourceReferenceError(messages.TASK_ASSIGNEE_NOT_FOUND)

    requested_ids = set(payload.tag_ids)
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(requested_ids))).all())
    if len(tags) != len(requested_ids):
        raise InvalidResourceReferenceError(messages.TASK_TAGS_INVALID)

    task = Task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
        tags=tags,
    )
    db.add(task)
    commit_or_rollback(db)
    statement = select(Task).where(Task.id == task.id).options(selectinload(Task.tags))
    return db.scalars(statement).one()
