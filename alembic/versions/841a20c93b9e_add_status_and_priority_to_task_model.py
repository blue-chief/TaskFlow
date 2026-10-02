"""add status and priority to Task model

Revision ID: 841a20c93b9e
Revises: 87222e96154e
Create Date: 2026-10-02 12:58:54.208029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '841a20c93b9e'
down_revision: Union[str, Sequence[str], None] = '87222e96154e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    status_enum = sa.Enum(
        "todo",
        "in_progress",
        "completed",
        "cancelled",
        name="taskstatusenum",
    )

    priority_enum = sa.Enum(
        "low",
        "medium",
        "high",
        "urgent",
        name="taskpriorityenum",
    )

    status_enum.create(op.get_bind(), checkfirst=True)
    priority_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "tasks",
        sa.Column("status", status_enum, nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("priority", priority_enum, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "status")

    priority_enum = sa.Enum(
        "low",
        "medium",
        "high",
        "urgent",
        name="taskpriorityenum",
    )

    status_enum = sa.Enum(
        "todo",
        "in_progress",
        "completed",
        "cancelled",
        name="taskstatusenum",
    )

    priority_enum.drop(op.get_bind(), checkfirst=True)
    status_enum.drop(op.get_bind(), checkfirst=True)
