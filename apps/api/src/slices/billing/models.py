import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class PlanTier(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingTargetType(enum.StrEnum):
    WORKSPACE = "workspace"
    PERSONAL = "personal"


class SubscriptionStatus(enum.StrEnum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class PaymentMethod(enum.StrEnum):
    PIX = "pix"
    BOLETO = "boleto"
    CREDIT_CARD = "credit_card"


class Subscription(Base):
    __tablename__ = "subscriptions"

    target_type: Mapped[str] = mapped_column(String(20), default=BillingTargetType.WORKSPACE, nullable=False)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    plan_tier: Mapped[str] = mapped_column(String(50), default=PlanTier.FREE, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=SubscriptionStatus.ACTIVE, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="mercadopago", nullable=False)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Quotas e limites do plano
    max_projects: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    invoices: Mapped[list["PaymentInvoice"]] = relationship(
        "PaymentInvoice", back_populates="subscription", cascade="all, delete-orphan"
    )


class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # Ex: 4900 = R$ 49,00
    currency: Mapped[str] = mapped_column(String(10), default="BRL", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, paid, failed
    payment_method: Mapped[str] = mapped_column(String(50), default=PaymentMethod.PIX, nullable=False)

    # Dados de cobrança Mercado Pago (Pix / Boleto)
    pix_qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    pix_copy_paste: Mapped[str | None] = mapped_column(Text, nullable=True)
    boleto_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    boleto_barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)

    provider_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="invoices")
