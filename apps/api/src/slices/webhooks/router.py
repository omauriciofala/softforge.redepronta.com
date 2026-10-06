import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.webhooks.schemas import (
    WebhookDeliveryListResponse,
    WebhookDeliveryResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
)
from src.slices.webhooks.service import (
    create_webhook_endpoint,
    delete_webhook_endpoint,
    get_webhook_endpoint,
    list_webhook_deliveries,
    list_webhook_endpoints,
    update_webhook_endpoint,
)
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/webhooks", tags=["Webhooks Outbound"])


@router.post(
    "",
    response_model=WebhookEndpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar endpoint de webhook",
    description="Registra uma nova URL receptora no workspace e gera um segredo criptográfico HMAC SHA256 exclusivo.",
)
async def create_endpoint(
    workspace_id: uuid.UUID,
    req: WebhookEndpointCreate,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookEndpointResponse:
    endpoint = await create_webhook_endpoint(session, workspace_id, req)
    return WebhookEndpointResponse.model_validate(endpoint)


@router.get(
    "",
    response_model=list[WebhookEndpointResponse],
    summary="Listar webhooks do workspace",
    description="Retorna todos os webhooks configurados para o workspace informado.",
)
async def list_endpoints(
    workspace_id: uuid.UUID,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[WebhookEndpointResponse]:
    endpoints = await list_webhook_endpoints(session, workspace_id)
    return [WebhookEndpointResponse.model_validate(ep) for ep in endpoints]


@router.get(
    "/{endpoint_id}",
    response_model=WebhookEndpointResponse,
    summary="Obter detalhes de um webhook",
    description="Retorna as configurações e o segredo de um webhook específico do workspace.",
)
async def get_endpoint(
    workspace_id: uuid.UUID,
    endpoint_id: uuid.UUID,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookEndpointResponse:
    endpoint = await get_webhook_endpoint(session, endpoint_id, workspace_id)
    return WebhookEndpointResponse.model_validate(endpoint)


@router.patch(
    "/{endpoint_id}",
    response_model=WebhookEndpointResponse,
    summary="Atualizar webhook",
    description="Modifica a URL, eventos inscritos ou status de ativação de um webhook.",
)
async def update_endpoint(
    workspace_id: uuid.UUID,
    endpoint_id: uuid.UUID,
    req: WebhookEndpointUpdate,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookEndpointResponse:
    endpoint = await update_webhook_endpoint(session, endpoint_id, workspace_id, req)
    return WebhookEndpointResponse.model_validate(endpoint)


@router.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover webhook",
    description="Exclui o endpoint de webhook e todo o seu histórico de entregas.",
)
async def delete_endpoint(
    workspace_id: uuid.UUID,
    endpoint_id: uuid.UUID,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await delete_webhook_endpoint(session, endpoint_id, workspace_id)


@router.get(
    "/{endpoint_id}/deliveries",
    response_model=WebhookDeliveryListResponse,
    summary="Listar histórico de entregas do webhook",
    description="Retorna as tentativas de entrega de eventos para o webhook com status HTTP e payloads.",
)
async def list_deliveries(
    workspace_id: uuid.UUID,
    endpoint_id: uuid.UUID,
    _member: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> WebhookDeliveryListResponse:
    items, total = await list_webhook_deliveries(
        session=session,
        endpoint_id=endpoint_id,
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
    )
    return WebhookDeliveryListResponse(
        items=[WebhookDeliveryResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
