import secrets
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundException
from src.core.queue import get_queue
from src.slices.webhooks.models import WebhookDelivery, WebhookEndpoint
from src.slices.webhooks.schemas import WebhookEndpointCreate, WebhookEndpointUpdate


async def create_webhook_endpoint(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    req: WebhookEndpointCreate,
) -> WebhookEndpoint:
    """Cadastra um novo webhook para o workspace gerando segredo HMAC exclusivo."""
    endpoint = WebhookEndpoint(
        workspace_id=workspace_id,
        url=req.url,
        description=req.description,
        secret=f"whsec_{secrets.token_hex(24)}",
        events=req.events or ["*"],
        is_active=True,
    )
    session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)
    return endpoint


async def list_webhook_endpoints(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[WebhookEndpoint]:
    """Retorna todos os webhooks configurados no workspace."""
    stmt = (
        select(WebhookEndpoint)
        .where(WebhookEndpoint.workspace_id == workspace_id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_webhook_endpoint(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> WebhookEndpoint:
    """Obtém detalhes do endpoint validando o workspace proprietário."""
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise NotFoundException(message="Endpoint de webhook não encontrado.")
    return endpoint


async def update_webhook_endpoint(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    workspace_id: uuid.UUID,
    req: WebhookEndpointUpdate,
) -> WebhookEndpoint:
    """Atualiza configurações de um webhook existente."""
    endpoint = await get_webhook_endpoint(session, endpoint_id, workspace_id)

    if req.url is not None:
        endpoint.url = req.url
    if req.description is not None:
        endpoint.description = req.description
    if req.events is not None:
        endpoint.events = req.events
    if req.is_active is not None:
        endpoint.is_active = req.is_active

    await session.commit()
    await session.refresh(endpoint)
    return endpoint


async def delete_webhook_endpoint(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> None:
    """Remove um endpoint de webhook e seu histórico de entregas associado."""
    endpoint = await get_webhook_endpoint(session, endpoint_id, workspace_id)
    await session.delete(endpoint)
    await session.commit()


async def trigger_webhook_event(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
) -> list[WebhookDelivery]:
    """Dispara assincronamente um evento para todos os endpoints do workspace que assinam este evento."""
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.workspace_id == workspace_id,
        WebhookEndpoint.is_active == True,  # noqa: E712
    )
    res = await session.execute(stmt)
    endpoints = list(res.scalars().all())

    matching_endpoints = [
        ep for ep in endpoints if "*" in ep.events or event_type in ep.events
    ]

    if not matching_endpoints:
        return []

    queue = await get_queue()
    deliveries: list[WebhookDelivery] = []

    for ep in matching_endpoints:
        delivery = WebhookDelivery(
            endpoint_id=ep.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempt=1,
        )
        session.add(delivery)
        await session.flush()
        deliveries.append(delivery)

        # Enfileira tentativa de despacho assíncrona no Arq
        await queue.enqueue("dispatch_webhook_task", delivery_id=str(delivery.id), attempt=1)

    await session.commit()
    return deliveries


async def list_webhook_deliveries(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    workspace_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[WebhookDelivery], int]:
    """Lista histórico paginado de entregas para um endpoint do workspace."""
    # Valida que o endpoint pertence ao workspace
    await get_webhook_endpoint(session, endpoint_id, workspace_id)

    base_query = select(WebhookDelivery).where(WebhookDelivery.endpoint_id == endpoint_id)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_res = await session.execute(count_query)
    total = total_res.scalar_one()

    query = (
        base_query.order_by(WebhookDelivery.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(query)
    items = list(result.scalars().all())

    return items, total
