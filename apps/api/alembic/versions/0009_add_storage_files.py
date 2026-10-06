"""Add stored_files table for local and S3/MinIO file management.

Revision ID: 0009_add_storage_files
Revises: 0008_add_workspace_invites
Create Date: 2026-10-06 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_add_storage_files"
down_revision: str | None = "0008_add_workspace_invites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stored_files",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "uploaded_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stored_files_id", "stored_files", ["id"])
    op.create_index("ix_stored_files_workspace_id", "stored_files", ["workspace_id"])
    op.create_index("ix_stored_files_uploaded_by_user_id", "stored_files", ["uploaded_by_user_id"])
    op.create_index("ix_stored_files_is_public", "stored_files", ["is_public"])


def downgrade() -> None:
    op.drop_table("stored_files")
