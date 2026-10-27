from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.core import messages
from app.core.exceptions import ResourceNotFoundError
from app.crud.transactions import commit_or_rollback
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate
from app.schemas.common import PaginationParams


def list_task_comments(
    db: Session, task_id: int, pagination: PaginationParams
) -> tuple[list[Comment], int]:
    if db.get(Task, task_id) is None:
        raise ResourceNotFoundError(messages.TASK_NOT_FOUND)

    statement = (
        select(Comment)
        .where(Comment.task_id == task_id)
        .order_by(Comment.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    total = (
        db.scalar(select(func.count(Comment.id)).where(Comment.task_id == task_id))
        or 0
    )
    return list(db.scalars(statement).all()), total


def create_task_comment(
    db: Session, task_id: int, author: User, payload: CommentCreate
) -> tuple[Comment, Task]:
    statement = (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.project).selectinload(Project.owner),
        )
        .with_for_update()
    )
    task = db.scalars(statement).one_or_none()
    if task is None:
        raise ResourceNotFoundError(messages.TASK_NOT_FOUND)

    comment = Comment(content=payload.content, task=task, author=author)
    db.add(comment)
    try:
        commit_or_rollback(db)
    except IntegrityError:
        if db.get(Task, task_id) is None:
            raise ResourceNotFoundError(messages.TASK_NOT_FOUND)
        raise
    db.refresh(comment)
    return comment, task


def _lock_task_comment(db: Session, comment: Comment) -> Comment:
    statement = (
        select(Comment)
        .where(Comment.id == comment.id)
        .with_for_update(of=Comment)
        .execution_options(populate_existing=True)
    )
    locked_comment = db.scalars(statement).one_or_none()
    if locked_comment is None:
        raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
    return locked_comment


def _commit_comment_mutation(db: Session) -> None:
    try:
        commit_or_rollback(db)
    except StaleDataError:
        raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND) from None


def update_task_comment(
    db: Session,
    comment: Comment,
    payload: CommentUpdate,
) -> Comment:
    comment = _lock_task_comment(db, comment)
    comment.content = payload.content
    _commit_comment_mutation(db)
    return comment


def delete_task_comment(
    db: Session, comment: Comment
) -> None:
    comment = _lock_task_comment(db, comment)
    result = db.execute(delete(Comment).where(Comment.id == comment.id))
    if result.rowcount == 0:
        db.rollback()
        raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
    _commit_comment_mutation(db)
