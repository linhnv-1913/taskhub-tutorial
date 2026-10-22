from sqlalchemy import Column, DateTime, ForeignKey, Index, Table, func

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
    Index("ix_task_bookmarks_task_id", "task_id"),
)
