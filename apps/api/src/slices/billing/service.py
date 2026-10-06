import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, NotFoundException
from src.slices.billing.models import (
    BillingTargetType,
    PaymentInvoice,
    PaymentMethod,
    PlanTier,
    Subscription,
    SubscriptionStatus,
)
from src.slices.billing.providers import MercadoPagoGateway
from src.slices.billing.schemas import CheckoutRequest, PlanDefinitionResponse

# Catálogo oficial de planos do SoftForge
PLAN_CATALOG: dict[PlanTier, dict[str, Any]] = {
    PlanTier.FREE: {
        "tier": PlanTier.FREE,
        "name": "Plano Starter (Gratuito)",
        "price_cents": 0,
        "max_projects": 3,
        "max_members": 2,
        "features": [
            "Até 3 projetos simultâneos",
            "Até 2 membros por workspace",
            "Autenticação JWT completa",
            "Suporte da comunidade",
        ],
    },
    PlanTier.PRO: {
        "tier": PlanTier.PRO,
        "name": "Plano Profissional",
        "price_cents": 4900,  # R$ 49,00 / mês
        "max_projects": 25,
        "max_members": 10,
        "features": [
            "Até 25 projetos",
            "Até 10 membros por workspace",
            "Exportação OpenAPI e Webhooks",
            "Suporte prioritário",
        ],
    },
    PlanTier.ENTERPRISE: {
        "tier": PlanTier.ENTERPRISE,
        "name": "Plano Empresarial",
        "price_cents": 19900,  # R$ 199,00 / mês
        "max_projects": -1,  # Ilimitado
        "max_members": -1,  # Ilimitado
        "features": [
            "Projetos e membros ilimitados",
            "Múltiplos administradores e RBAC avançado",
            "Logs de auditoria e conformidade",
            "SLA garantido de 99.9%",
        ],
    },
}


def get_available_plans() -> list[PlanDefinitionResponse]:
    """Retorna os planos e preços vigentes."""
    return [PlanDefinitionResponse(**data) for data in PLAN_CATALOG.values()]


async def get_or_create_subscription(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID | None = None,
    target_type: BillingTargetType = BillingTargetType.WORKSPACE,
) -> Subscription:
    """Busca a assinatura ativa ou provisiona o plano Free padrão."""
    if target_type == BillingTargetType.WORKSPACE and workspace_id:
        stmt = select(Subscription).where(
            Subscription.workspace_id == workspace_id,
            Subscription.status != SubscriptionStatus.CANCELED,
        )
    else:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.target_type == BillingTargetType.PERSONAL,
            Subscription.status != SubscriptionStatus.CANCELED,
        )

    res = await session.execute(stmt)
    subscription = res.scalar_one_or_none()

    if not subscription:
        free_plan = PLAN_CATALOG[PlanTier.FREE]
        subscription = Subscription(
            target_type=target_type,
            workspace_id=workspace_id if target_type == BillingTargetType.WORKSPACE else None,
            user_id=user_id,
            plan_tier=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            max_projects=free_plan["max_projects"],
            max_members=free_plan["max_members"],
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=365 * 10),  # Free permanente
        )
        session.add(subscription)
        await session.flush()

    return subscription


async def create_checkout(
    session: AsyncSession,
    user_id: uuid.UUID,
    request: CheckoutRequest,
    gateway: MercadoPagoGateway | None = None,
) -> tuple[Subscription, PaymentInvoice, str]:
    """Inicia o processo de checkout gerando fatura Pix/Boleto no Mercado Pago."""
    if request.plan_tier == PlanTier.FREE:
        raise AppException("O plano gratuito não requer checkout ou cobrança.", status_code=400)

    plan_info = PLAN_CATALOG.get(request.plan_tier)
    if not plan_info:
        raise NotFoundException("Plano selecionado não encontrado")

    subscription = await get_or_create_subscription(
        session=session,
        user_id=user_id,
        workspace_id=request.workspace_id,
        target_type=request.target_type,
    )

    # Cria fatura de cobrança pendente
    invoice = PaymentInvoice(
        subscription_id=subscription.id,
        amount_cents=plan_info["price_cents"],
        currency="BRL",
        status="pending",
        payment_method=request.payment_method,
    )
    session.add(invoice)
    await session.flush()

    # Integra com o gateway (Mercado Pago ou Mock offline)
    gw = gateway or MercadoPagoGateway()
    charge_data = await gw.create_charge(
        invoice=invoice,
        payer_email=request.payer_email,
        payer_cpf_cnpj=request.payer_cpf_cnpj,
    )

    invoice.provider_payment_id = charge_data.get("provider_payment_id")
    invoice.pix_qr_code = charge_data.get("pix_qr_code")
    invoice.pix_copy_paste = charge_data.get("pix_copy_paste")
    invoice.boleto_url = charge_data.get("boleto_url")
    invoice.boleto_barcode = charge_data.get("boleto_barcode")

    # Se for aprovado instantaneamente (ex: cartão de crédito mock)
    if charge_data.get("status") == "paid":
        await activate_subscription_plan(
            session=session,
            subscription=subscription,
            invoice=invoice,
            new_plan=request.plan_tier,
        )

    await session.flush()

    message = (
        "Pix gerado com sucesso. Utilize o Copia e Cola para pagar no seu app bancário."
        if request.payment_method == PaymentMethod.PIX
        else "Boleto bancário emitido. O prazo de compensação é de até 3 dias úteis."
    )

    return subscription, invoice, message


async def activate_subscription_plan(
    session: AsyncSession,
    subscription: Subscription,
    invoice: PaymentInvoice,
    new_plan: PlanTier,
) -> None:
    """Atualiza a assinatura para o novo plano após confirmação do pagamento."""
    plan_info = PLAN_CATALOG[new_plan]
    now = datetime.now(UTC)

    subscription.plan_tier = new_plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.max_projects = plan_info["max_projects"]
    subscription.max_members = plan_info["max_members"]
    subscription.current_period_start = now
    subscription.current_period_end = now + timedelta(days=30)  # Recorrência mensal

    invoice.status = "paid"
    invoice.paid_at = now
    logger.info(f"Assinatura {subscription.id} ativada no plano {new_plan} via fatura {invoice.id}")


async def process_mercadopago_webhook(
    session: AsyncSession,
    payload: dict[str, Any],
    gateway: MercadoPagoGateway | None = None,
) -> bool:
    """Processa webhooks de pagamento enviados pelo Mercado Pago."""
    data = payload.get("data", {})
    payment_id = str(data.get("id") or payload.get("id") or "")
    logger.debug(f"Processando webhook Mercado Pago (tipo: {payload.get('action') or payload.get('type')})")

    if not payment_id:
        logger.warning(f"Webhook Mercado Pago recebido sem ID de pagamento: {payload}")
        return False

    stmt = select(PaymentInvoice).where(PaymentInvoice.provider_payment_id == payment_id)
    res = await session.execute(stmt)
    invoice = res.scalar_one_or_none()

    if not invoice:
        logger.info(f"Webhook recebido para pagamento não rastreado no SoftForge: {payment_id}")
        return False

    gw = gateway or MercadoPagoGateway()
    status_data = await gw.fetch_payment_status(payment_id)
    payment_status = status_data.get("status")

    if payment_status in ("approved", "paid"):
        sub_stmt = select(Subscription).where(Subscription.id == invoice.subscription_id)
        sub_res = await session.execute(sub_stmt)
        subscription = sub_res.scalar_one_or_none()

        if subscription:
            # Identifica o plano pelo valor pago
            matched_plan = PlanTier.PRO
            for tier, info in PLAN_CATALOG.items():
                if info["price_cents"] == invoice.amount_cents:
                    matched_plan = tier
                    break

            await activate_subscription_plan(
                session=session,
                subscription=subscription,
                invoice=invoice,
                new_plan=matched_plan,
            )
            return True

    return False
