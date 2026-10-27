from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.crud.comments import create_task_comment
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services.comment_notifications import (
    build_comment_notification,
    send_task_comment_notification,
)


def create_comment_with_notification(
    db: Session,
    task_id: int,
    author: User,
    payload: CommentCreate,
    background_tasks: BackgroundTasks,
) -> Comment:
    comment, task = create_task_comment(db, task_id, author, payload)
    notification = build_comment_notification(task, author, comment)
    if notification is not None:
        background_tasks.add_task(send_task_comment_notification, notification)
    return comment
