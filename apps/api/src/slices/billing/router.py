import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.billing.models import BillingTargetType
from src.slices.billing.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceResponse,
    PlanDefinitionResponse,
    SubscriptionResponse,
)
from src.slices.billing.service import (
    create_checkout,
    get_available_plans,
    get_or_create_subscription,
    process_mercadopago_webhook,
)

router = APIRouter(
    prefix="/billing",
    tags=["Assinaturas & Faturamento (Mercado Pago)"],
)


@router.get(
    "/plans",
    response_model=list[PlanDefinitionResponse],
    summary="Listar Planos Disponíveis",
    description="Retorna a lista de planos (Free, Pro, Enterprise), preços e limites de quotas vigentes.",
)
async def list_plans() -> list[PlanDefinitionResponse]:
    return get_available_plans()


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Consultar Assinatura Vigente",
    description="Retorna o status, plano e limites de quotas do Workspace ou Usuário autenticado.",
)
async def get_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: uuid.UUID | None = Query(None, description="ID do workspace a consultar"),
) -> SubscriptionResponse:
    target_type = BillingTargetType.WORKSPACE if workspace_id else BillingTargetType.PERSONAL
    subscription = await get_or_create_subscription(
        session=session,
        user_id=current_user.id,
        workspace_id=workspace_id,
        target_type=target_type,
    )
    return SubscriptionResponse.model_validate(subscription)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Checkout de Assinatura (Pix / Boleto / Cartão)",
    description="Emite fatura e dados de pagamento via Mercado Pago (QR Code Pix Copia e Cola ou código de barras).",
)
async def checkout(
    request_data: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CheckoutResponse:
    subscription, invoice, message = await create_checkout(
        session=session,
        user_id=current_user.id,
        request=request_data,
    )

    return CheckoutResponse(
        subscription=SubscriptionResponse.model_validate(subscription),
        invoice=InvoiceResponse.model_validate(invoice),
        message=message,
    )


@router.post(
    "/webhooks/mercadopago",
    status_code=status.HTTP_200_OK,
    summary="Webhook de Notificações do Mercado Pago",
    description="Recebe notificações assíncronas de pagamentos Pix, Boleto ou Cartão para ativar assinaturas.",
)
async def mercadopago_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    payload: dict[str, Any] = await request.json()
    success = await process_mercadopago_webhook(session=session, payload=payload)
    return {"received": True, "processed": success}
