"""Add workspace_themes table for themes and white-labeling.

Revision ID: 0011_add_workspace_themes
Revises: 0010_add_feature_flags
Create Date: 2026-10-06 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_add_workspace_themes"
down_revision: str | None = "0010_add_feature_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_themes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("theme_slug", sa.String(length=100), server_default="default-react", nullable=False),
        sa.Column("custom_logo_url", sa.String(length=500), nullable=True),
        sa.Column("custom_primary_color", sa.String(length=50), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("tokens_override", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", name="uq_workspace_themes_workspace_id"),
    )
    op.create_index("ix_workspace_themes_id", "workspace_themes", ["id"])
    op.create_index("ix_workspace_themes_workspace_id", "workspace_themes", ["workspace_id"], unique=True)


def downgrade() -> None:
    op.drop_table("workspace_themes")
