"""Add oauth_accounts table and make user hashed_password nullable.

Revision ID: 0003_add_oauth_accounts
Revises: 0002_add_billing_subscriptions
Create Date: 2026-10-06 02:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_oauth_accounts"
down_revision: str | None = "0002_add_billing_subscriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Altera users para suportar avatar e permitir senha nula (OAuth puro)
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))
    op.alter_column("users", "hashed_password", existing_type=sa.String(length=255), nullable=True)

    # 2. Cria tabela oauth_accounts
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index(op.f("ix_oauth_accounts_id"), "oauth_accounts", ["id"], unique=False)
    op.create_index(op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_oauth_accounts_provider_user_id"), "oauth_accounts", ["provider_user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("oauth_accounts")
    op.alter_column("users", "hashed_password", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("users", "avatar_url")
