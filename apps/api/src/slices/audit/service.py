import uuid

from fastapi import Request
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.queue import get_queue
from src.slices.audit.models import AuditLog


async def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    workspace_id: uuid.UUID | str | None = None,
    user_id: uuid.UUID | str | None = None,
    user_email: str | None = None,
    request: Request | None = None,
) -> str | None:
    """Enfileira de forma assíncrona um evento de auditoria com latência zero para a requisição."""
    ip_address = None
    user_agent = None

    if request:
        # Extrai IP real considerando headers de proxy reverso padrão
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host

        user_agent = request.headers.get("user-agent")

    queue = await get_queue()
    try:
        job_id = await queue.enqueue(
            "record_audit_log_task",
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return job_id
    except Exception as exc:
        logger.warning(f"[Audit] Falha ao enfileirar log de auditoria ({exc}). Continuando sem bloqueio.")
        return None


async def list_audit_logs(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    action: str | None = None,
    resource_type: str | None = None,
    user_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditLog], int]:
    """Consulta paginada da trilha imutável de auditoria de um workspace."""
    base_query = select(AuditLog).where(AuditLog.workspace_id == workspace_id)

    if action:
        base_query = base_query.where(AuditLog.action == action)
    if resource_type:
        base_query = base_query.where(AuditLog.resource_type == resource_type)
    if user_id:
        base_query = base_query.where(AuditLog.user_id == user_id)

    # Contagem total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Paginação ordenada do mais recente para o mais antigo
    query = (
        base_query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(query)
    items = list(result.scalars().all())

    return items, total
