"""Add dev_tasks and dev_task_notes tables for autonomous AI development task management.

Revision ID: 0012_add_dev_tasks
Revises: 0011_add_workspace_themes
Create Date: 2026-10-07 18:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0012_add_dev_tasks"
down_revision: str | None = "0011_add_workspace_themes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dev_tasks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=50), server_default="feature", nullable=False),
        sa.Column("priority", sa.String(length=50), server_default="medium", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="todo", nullable=False),
        sa.Column("target_files", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("verification_command", sa.String(length=500), nullable=True),
        sa.Column("verification_output", sa.Text(), nullable=True),
        sa.Column("git_branch", sa.String(length=100), nullable=True),
        sa.Column("assigned_agent", sa.String(length=100), nullable=True),
        sa.Column(
            "created_by_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dev_tasks_id", "dev_tasks", ["id"])
    op.create_index("ix_dev_tasks_workspace_id", "dev_tasks", ["workspace_id"])
    op.create_index("ix_dev_tasks_project_id", "dev_tasks", ["project_id"])
    op.create_index("ix_dev_tasks_status", "dev_tasks", ["status"])

    op.create_table(
        "dev_task_notes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "task_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("dev_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author", sa.String(length=100), nullable=False),
        sa.Column("note_type", sa.String(length=50), server_default="progress", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dev_task_notes_id", "dev_task_notes", ["id"])
    op.create_index("ix_dev_task_notes_task_id", "dev_task_notes", ["task_id"])


def downgrade() -> None:
    op.drop_table("dev_task_notes")
    op.drop_table("dev_tasks")
