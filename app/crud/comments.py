from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.core import messages
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError, ResourceNotFoundError
from app.crud.transactions import commit_or_rollback
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate


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


def _get_task_comment(db: Session, task_id: int, comment_id: int) -> Comment:
    statement = (
        select(Comment)
        .where(Comment.task_id == task_id, Comment.id == comment_id)
        .with_for_update()
    )
    comment = db.scalars(statement).one_or_none()
    if comment is None:
        raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
    return comment


def _ensure_comment_editor(comment: Comment, actor: User) -> None:
    if comment.author_id == actor.id or actor.role in {
        UserRole.ADMIN,
        UserRole.PM,
    }:
        return
    raise ForbiddenError(messages.TASK_COMMENT_AUTHOR_REQUIRED)


def _commit_comment_mutation(
    db: Session, task_id: int, comment_id: int
) -> None:
    try:
        commit_or_rollback(db)
    except (IntegrityError, StaleDataError):
        comment_exists = db.scalar(
            select(Comment.id).where(
                Comment.task_id == task_id,
                Comment.id == comment_id,
            )
        )
        if comment_exists is None:
            raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
        raise


def update_task_comment(
    db: Session,
    task_id: int,
    comment_id: int,
    actor: User,
    payload: CommentUpdate,
) -> Comment:
    comment = _get_task_comment(db, task_id, comment_id)
    _ensure_comment_editor(comment, actor)
    comment.content = payload.content
    _commit_comment_mutation(db, task_id, comment_id)
    return comment


def delete_task_comment(
    db: Session, task_id: int, comment_id: int, actor: User
) -> None:
    comment = _get_task_comment(db, task_id, comment_id)
    _ensure_comment_editor(comment, actor)
    try:
        result = db.execute(
            delete(Comment).where(
                Comment.task_id == task_id,
                Comment.id == comment_id,
            )
        )
        if result.rowcount != 1:
            db.rollback()
            raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
        commit_or_rollback(db)
    except (IntegrityError, StaleDataError):
        db.rollback()
        comment_exists = db.scalar(
            select(Comment.id).where(
                Comment.task_id == task_id,
                Comment.id == comment_id,
            )
        )
        if comment_exists is None:
            raise ResourceNotFoundError(messages.TASK_COMMENT_NOT_FOUND)
        raise
