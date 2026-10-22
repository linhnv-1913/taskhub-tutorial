from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FULL_NAME_MAX_LENGTH,
    USER_PASSWORD_HASH_MAX_LENGTH,
    USER_ROLE_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from app.core.enums import UserRole
from app.db.base import Base
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.project import Project
    from app.models.task import Task


class User(CreatedAtMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(USERNAME_MAX_LENGTH),
        unique=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(USER_EMAIL_MAX_LENGTH),
        unique=True,
        index=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(USER_FULL_NAME_MAX_LENGTH))
    password_hash: Mapped[str | None] = mapped_column(
        String(USER_PASSWORD_HASH_MAX_LENGTH)
    )
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            native_enum=False,
            length=USER_ROLE_MAX_LENGTH,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            validate_strings=True,
        ),
        default=UserRole.MEMBER,
        server_default=text("'MEMBER'"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
        nullable=False,
    )

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
