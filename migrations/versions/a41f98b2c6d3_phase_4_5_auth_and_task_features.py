"""Add authentication fields, task priority, and bookmarks.

Revision ID: a41f98b2c6d3
Revises: d2d8e0fe06a2
Create Date: 2026-10-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a41f98b2c6d3"
down_revision: str | Sequence[str] | None = "d2d8e0fe06a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255)))
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'MEMBER'"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.String(length=16),
            server_default=sa.text("'MEDIUM'"),
            nullable=False,
        ),
    )
    op.create_index("ix_tasks_priority", "tasks", ["priority"], unique=False)
    op.create_table(
        "task_bookmarks",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "task_id"),
    )
    op.create_index(
        "ix_task_bookmarks_task_id",
        "task_bookmarks",
        ["task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_bookmarks_task_id", table_name="task_bookmarks")
    op.drop_table("task_bookmarks")
    op.drop_index("ix_tasks_priority", table_name="tasks")
    op.drop_column("tasks", "priority")
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
