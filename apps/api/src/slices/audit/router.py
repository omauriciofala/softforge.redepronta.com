import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.audit.schemas import AuditLogListResponse, AuditLogResponse
from src.slices.audit.service import list_audit_logs
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces", tags=["Auditoria & Compliance"])


@router.get(
    "/{workspace_id}/audit-logs",
    response_model=AuditLogListResponse,
    summary="Listar trilha de auditoria do Workspace",
    description="Retorna o histórico imutável de eventos operacionais e de segurança. Requer papel mínimo de Administrador.",
)
async def get_workspace_audit_logs(
    workspace_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _member: Annotated[
        WorkspaceMember,
        Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    ],
    action: str | None = Query(None, description="Filtrar por nome da ação (ex: project.created)"),
    resource_type: str | None = Query(None, description="Filtrar por tipo de recurso (ex: project)"),
    user_id: uuid.UUID | None = Query(None, description="Filtrar por autor da ação"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> AuditLogListResponse:
    items, total = await list_audit_logs(
        session=session,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
