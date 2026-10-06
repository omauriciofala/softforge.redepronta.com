import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.slices.billing.models import BillingTargetType, PaymentMethod, PlanTier


class PlanFeature(BaseModel):
    name: str = Field(..., description="Nome da funcionalidade incluída")
    included: bool = Field(True, description="Se está inclusa no plano")


class PlanDefinitionResponse(BaseModel):
    tier: PlanTier = Field(..., description="Identificador do plano")
    name: str = Field(..., description="Nome comercial do plano")
    price_cents: int = Field(..., description="Preço mensal em centavos (BRL)")
    max_projects: int = Field(..., description="Limite de projetos permitidos (-1 para ilimitado)")
    max_members: int = Field(..., description="Limite de membros por workspace (-1 para ilimitado)")
    features: list[str] = Field(default_factory=list, description="Lista de benefícios inclusos")


class CheckoutRequest(BaseModel):
    target_type: BillingTargetType = Field(
        BillingTargetType.WORKSPACE,
        description="Assinatura pessoal ou corporativa (workspace)",
    )
    workspace_id: uuid.UUID | None = Field(
        None,
        description="Obrigatório caso target_type seja 'workspace'",
    )
    plan_tier: PlanTier = Field(
        PlanTier.PRO,
        description="Plano desejado para assinatura",
    )
    payment_method: PaymentMethod = Field(
        PaymentMethod.PIX,
        description="Método de pagamento (pix, boleto, credit_card)",
    )
    payer_email: EmailStr = Field(..., description="E-mail do pagador para recibo e notificações")
    payer_cpf_cnpj: str | None = Field(
        None,
        description="CPF ou CNPJ do pagador (necessário para emissão de Pix e Boleto)",
    )


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    amount_cents: int
    currency: str
    status: str
    payment_method: str
    provider_payment_id: str | None = None
    pix_qr_code: str | None = None
    pix_copy_paste: str | None = None
    boleto_url: str | None = None
    boleto_barcode: str | None = None
    paid_at: datetime | None = None
    created_at: datetime


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: str
    workspace_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    plan_tier: str
    status: str
    payment_method: str | None = None
    provider: str
    current_period_start: datetime
    current_period_end: datetime | None = None
    cancel_at_period_end: bool
    max_projects: int
    max_members: int
    created_at: datetime


class CheckoutResponse(BaseModel):
    subscription: SubscriptionResponse
    invoice: InvoiceResponse
    message: str = Field(..., description="Instruções de pagamento")


class MercadoPagoWebhookEvent(BaseModel):
    action: str | None = None
    type: str | None = None
    data: dict[str, Any] | None = None
    id: str | int | None = None
