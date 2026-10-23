import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommentNotification:
    recipient_email: str
    task_title: str
    commenter_name: str
    comment_content: str


def build_comment_notification(
    task: Task, author: User, comment: Comment
) -> CommentNotification | None:
    recipient = task.assignee or task.project.owner
    if recipient.id == author.id:
        return None
    return CommentNotification(
        recipient_email=recipient.email,
        task_title=task.title,
        commenter_name=author.full_name,
        comment_content=comment.content,
    )


def send_task_comment_notification(notification: CommentNotification) -> None:
    if settings.smtp_host is None or settings.smtp_from_email is None:
        logger.warning(
            "Task comment email skipped; SMTP_HOST and SMTP_FROM_EMAIL are required"
        )
        return

    try:
        message = EmailMessage()
        message["Subject"] = f"New comment on task: {notification.task_title}"
        message["From"] = str(settings.smtp_from_email)
        message["To"] = notification.recipient_email
        message.set_content(
            f"{notification.commenter_name} commented on "
            f"'{notification.task_title}':\n\n{notification.comment_content}"
        )

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as server:
            if settings.smtp_starttls:
                server.starttls(context=ssl.create_default_context())
            elif settings.smtp_username or settings.smtp_password is not None:
                raise ValueError("SMTP authentication requires STARTTLS")
            if settings.smtp_username or settings.smtp_password is not None:
                if settings.smtp_username is None or settings.smtp_password is None:
                    raise ValueError("SMTP username and password must be set together")
                server.login(
                    settings.smtp_username,
                    settings.smtp_password.get_secret_value(),
                )
            server.send_message(message)
    except Exception:
        logger.exception("Task comment email delivery failed")
