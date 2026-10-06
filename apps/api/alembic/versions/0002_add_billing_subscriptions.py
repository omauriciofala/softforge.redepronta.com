"""Add subscriptions and payment_invoices tables for billing slice.

Revision ID: 0002_add_billing_subscriptions
Revises: 0001_initial_baseline
Create Date: 2026-10-06 01:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_billing_subscriptions"
down_revision: str | None = "0001_initial_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tabela subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("target_type", sa.String(length=20), server_default="workspace", nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("plan_tier", sa.String(length=50), server_default="free", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("provider", sa.String(length=50), server_default="mercadopago", nullable=False),
        sa.Column("provider_subscription_id", sa.String(length=100), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=100), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("max_projects", sa.Integer(), server_default="3", nullable=False),
        sa.Column("max_members", sa.Integer(), server_default="2", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)
    op.create_index(op.f("ix_subscriptions_workspace_id"), "subscriptions", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_provider_subscription_id"), "subscriptions", ["provider_subscription_id"], unique=False)

    # 2. Tabela payment_invoices
    op.create_table(
        "payment_invoices",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("subscription_id", sa.Uuid(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="BRL", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("payment_method", sa.String(length=50), server_default="pix", nullable=False),
        sa.Column("pix_qr_code", sa.Text(), nullable=True),
        sa.Column("pix_copy_paste", sa.Text(), nullable=True),
        sa.Column("boleto_url", sa.Text(), nullable=True),
        sa.Column("boleto_barcode", sa.String(length=100), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=100), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_payment_invoices_id"), "payment_invoices", ["id"], unique=False)
    op.create_index(op.f("ix_payment_invoices_subscription_id"), "payment_invoices", ["subscription_id"], unique=False)
    op.create_index(op.f("ix_payment_invoices_provider_payment_id"), "payment_invoices", ["provider_payment_id"], unique=True)


def downgrade() -> None:
    op.drop_table("payment_invoices")
    op.drop_table("subscriptions")
