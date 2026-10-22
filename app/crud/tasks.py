from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import messages
from app.core.enums import TaskPriority, TaskStatus
from app.core.exceptions import (
    InvalidResourceReferenceError,
    ResourceNotFoundError,
)
from app.crud.transactions import commit_or_rollback
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task
from app.models.task_bookmarks import task_bookmarks
from app.models.user import User
from app.schemas.task import TaskCreate


def list_tasks(
    db: Session,
    status_filter: TaskStatus | None,
    priority_filter: TaskPriority | None,
    skip: int,
    limit: int,
) -> list[Task]:
    statement = select(Task).options(selectinload(Task.tags)).order_by(Task.id)
    if status_filter is not None:
        statement = statement.where(Task.status == status_filter)
    if priority_filter is not None:
        statement = statement.where(Task.priority == priority_filter)
    statement = statement.offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def list_project_tasks(
    db: Session, project_id: int, skip: int, limit: int
) -> list[Task]:
    if db.get(Project, project_id) is None:
        raise ResourceNotFoundError(messages.PROJECT_NOT_FOUND)
    statement = (
        select(Task)
        .where(Task.project_id == project_id)
        .options(selectinload(Task.tags))
        .order_by(Task.id)
        .offset(skip)
        .limit(limit)
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
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        tags=tags,
    )
    db.add(task)
    commit_or_rollback(db)
    statement = select(Task).where(Task.id == task.id).options(selectinload(Task.tags))
    return db.scalars(statement).one()


def bookmark_task(db: Session, user_id: int, task_id: int) -> bool:
    if db.get(Task, task_id) is None:
        raise ResourceNotFoundError(messages.TASK_NOT_FOUND)
    bookmark = select(task_bookmarks.c.task_id).where(
        task_bookmarks.c.user_id == user_id,
        task_bookmarks.c.task_id == task_id,
    )
    if db.scalar(bookmark) is not None:
        return False

    try:
        db.execute(
            insert(task_bookmarks).values(user_id=user_id, task_id=task_id)
        )
        commit_or_rollback(db)
    except IntegrityError:
        db.rollback()
        if db.get(Task, task_id) is None:
            raise ResourceNotFoundError(messages.TASK_NOT_FOUND)
        if db.scalar(bookmark) is not None:
            return False
        raise
    return True
