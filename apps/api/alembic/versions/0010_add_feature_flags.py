"""Add feature_flags and feature_flag_overrides tables for tenant toggles.

Revision ID: 0010_add_feature_flags
Revises: 0009_add_storage_files
Create Date: 2026-10-06 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_add_feature_flags"
down_revision: str | None = "0009_add_storage_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feature_flags_id", "feature_flags", ["id"])
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"], unique=True)

    op.create_table(
        "feature_flag_overrides",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "feature_flag_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("feature_flags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("feature_flag_id", "workspace_id", name="uq_feature_flag_workspace_override"),
    )
    op.create_index("ix_feature_flag_overrides_id", "feature_flag_overrides", ["id"])
    op.create_index("ix_feature_flag_overrides_feature_flag_id", "feature_flag_overrides", ["feature_flag_id"])
    op.create_index("ix_feature_flag_overrides_workspace_id", "feature_flag_overrides", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("feature_flag_overrides")
    op.drop_table("feature_flags")
