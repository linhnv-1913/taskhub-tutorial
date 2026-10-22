from sqlalchemy import Column, DateTime, ForeignKey, Table, func

from app.db.base import Base

task_bookmarks = Table(
    "task_bookmarks",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "task_id",
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
