import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.apikeys.schemas import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
)
from src.slices.apikeys.service import (
    count_api_keys,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.webhooks.service import trigger_webhook_event
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/api-keys", tags=["Chaves de API (PAT / M2M)"])


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar nova Chave de API / PAT",
    description=(
        "Gera uma chave secreta criptograficamente segura para chamadas M2M ou integração de agentes autônomos. "
        "O segredo em texto puro ('raw_key') é retornado EXCLUSIVAMENTE nesta chamada e nunca mais será exibido."
    ),
)
async def create(
    workspace_id: uuid.UUID,
    req: ApiKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> ApiKeyCreatedResponse:
    _ = membership
    api_key, raw_key = await create_api_key(session, workspace_id, current_user.id, req)

    # Registro de auditoria assíncrona
    await log_audit_event(
        action="api_key.created",
        resource_type="api_key",
        resource_id=str(api_key.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    # Disparo de webhook outbound
    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="api_key.created",
        payload={
            "api_key_id": str(api_key.id),
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "scopes": api_key.scopes,
            "created_by": str(current_user.id),
        },
    )

    return ApiKeyCreatedResponse(
        id=api_key.id,
        workspace_id=api_key.workspace_id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        is_revoked=api_key.is_revoked,
        revoked_at=api_key.revoked_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="Listar Chaves de API do Workspace",
    description="Retorna todas as chaves de API do workspace com prefixos mascarados. Requer privilégio de Administrador.",
)
async def list_keys(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyListResponse:
    _ = membership
    items = await list_api_keys(session, workspace_id)
    total = await count_api_keys(session, workspace_id)
    return ApiKeyListResponse(
        items=[ApiKeyResponse.model_validate(k) for k in items],
        total=total,
    )


@router.delete(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Revogar Chave de API",
    description="Invalida imediatamente uma chave de API. Qualquer requisição futura utilizando-a receberá HTTP 401 Unauthorized.",
)
async def revoke(
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> ApiKeyResponse:
    _ = membership
    api_key = await revoke_api_key(session, workspace_id, key_id)

    # Registro de auditoria assíncrona
    await log_audit_event(
        action="api_key.revoked",
        resource_type="api_key",
        resource_id=str(api_key.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    # Disparo de webhook outbound
    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="api_key.revoked",
        payload={
            "api_key_id": str(api_key.id),
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "revoked_by": str(current_user.id),
        },
    )

    return ApiKeyResponse.model_validate(api_key)
