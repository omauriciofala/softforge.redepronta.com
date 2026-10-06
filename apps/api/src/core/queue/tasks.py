from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import delete

from src.core.database import AsyncSessionLocal
from src.slices.auth.models import RefreshToken


async def send_transactional_email(
    ctx: dict[str, Any],
    to_email: str,
    subject: str,
    body_html: str,
) -> dict[str, Any]:
    """Tarefa em segundo plano para envio de e-mails transacionais."""
    logger.info(f"[Task:send_transactional_email] Enviando e-mail para '{to_email}' com assunto '{subject}'")

    # Em ambiente de dev/mock, registramos o envio
    # Em produção, aqui integraria com Amazon SES, Resend, Sendgrid ou SMTP
    dispatched_at = datetime.now(UTC).isoformat()
    return {
        "status": "sent",
        "to_email": to_email,
        "subject": subject,
        "dispatched_at": dispatched_at,
    }


async def process_subscription_renewal(
    ctx: dict[str, Any],
    subscription_id: str,
) -> dict[str, Any]:
    """Tarefa em segundo plano para reconciliação e renovação de assinaturas."""
    logger.info(f"[Task:process_subscription_renewal] Verificando assinatura {subscription_id}")
    processed_at = datetime.now(UTC).isoformat()
    return {
        "status": "processed",
        "subscription_id": subscription_id,
        "processed_at": processed_at,
    }


async def cleanup_revoked_tokens(ctx: dict[str, Any]) -> dict[str, Any]:
    """Tarefa periódica/cron para limpeza de refresh tokens revogados ou expirados."""
    logger.info("[Task:cleanup_revoked_tokens] Iniciando expurgo de tokens inválidos...")
    now = datetime.now(UTC)

    session_maker = ctx.get("session_maker", AsyncSessionLocal)
    async with session_maker() as session:
        statement = delete(RefreshToken).where(
            (RefreshToken.revoked == True) | (RefreshToken.expires_at < now)  # noqa: E712
        )
        result = await session.execute(statement)
        await session.commit()
        deleted_count = result.rowcount or 0

    logger.info(f"[Task:cleanup_revoked_tokens] Removidos {deleted_count} tokens expirados/revogados.")
    return {"deleted_count": deleted_count, "executed_at": now.isoformat()}


async def record_audit_log_task(
    ctx: dict[str, Any],
    workspace_id: str | None = None,
    user_id: str | None = None,
    user_email: str | None = None,
    action: str = "",
    resource_type: str = "",
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """Tarefa em segundo plano para persistência desacoplada de logs de auditoria."""
    import uuid

    from src.slices.audit.models import AuditLog

    session_maker = ctx.get("session_maker", AsyncSessionLocal)
    async with session_maker() as session:
        log_entry = AuditLog(
            workspace_id=uuid.UUID(workspace_id) if workspace_id else None,
            user_id=uuid.UUID(user_id) if user_id else None,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
        )
        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)
        logger.info(f"[Task:record_audit_log_task] Log registrado [id={log_entry.id}, action={action}]")
        return {"status": "recorded", "id": str(log_entry.id), "action": action}


async def dispatch_webhook_task(
    ctx: dict[str, Any],
    delivery_id: str,
    attempt: int = 1,
) -> dict[str, Any]:
    """Despacha uma tentativa de entrega HTTP de webhook com assinatura HMAC-SHA256."""
    import uuid

    import httpx
    from sqlalchemy import select

    from src.slices.webhooks.models import WebhookDelivery, WebhookEndpoint
    from src.slices.webhooks.security import generate_webhook_signature

    session_maker = ctx.get("session_maker", AsyncSessionLocal)
    async with session_maker() as session:
        stmt = (
            select(WebhookDelivery, WebhookEndpoint)
            .join(WebhookEndpoint, WebhookDelivery.endpoint_id == WebhookEndpoint.id)
            .where(WebhookDelivery.id == uuid.UUID(delivery_id))
        )
        res = await session.execute(stmt)
        row = res.first()
        if not row:
            logger.warning(f"[Task:dispatch_webhook_task] Delivery {delivery_id} não encontrada.")
            return {"status": "not_found", "delivery_id": delivery_id}

        delivery, endpoint = row

        if not endpoint.is_active:
            delivery.status = "failed"
            delivery.error_message = "Webhook endpoint desativado."
            await session.commit()
            return {"status": "canceled", "delivery_id": delivery_id}

        sig_header = generate_webhook_signature(endpoint.secret, delivery.payload)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SoftForge-Webhooks/1.0",
            "X-SoftForge-Signature": sig_header,
            "X-SoftForge-Event": delivery.event_type,
            "X-SoftForge-Delivery": str(delivery.id),
        }

        # Offline / Mock transport fallback para testes determinísticos
        if (
            endpoint.url.startswith("mock://")
            or endpoint.url.startswith("https://mock.")
            or endpoint.url.startswith("http://mock.")
        ):
            delivery.status = "success"
            delivery.response_status_code = 200
            delivery.response_body = '{"received": true, "mock": true}'
            delivery.delivered_at = datetime.now(UTC)
            delivery.attempt = attempt
            await session.commit()
            logger.info(f"[Task:dispatch_webhook_task] Mock delivery {delivery_id} entregue com sucesso.")
            return {"status": "success", "delivery_id": delivery_id}

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.post(endpoint.url, json=delivery.payload, headers=headers)
                delivery.response_status_code = response.status_code
                delivery.response_body = response.text[:1000]
                delivery.attempt = attempt

                if 200 <= response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.now(UTC)
                    await session.commit()
                    logger.info(
                        f"[Task:dispatch_webhook_task] Delivery {delivery_id} enviada com sucesso HTTP {response.status_code}."
                    )
                    return {"status": "success", "delivery_id": delivery_id}
                else:
                    delivery.status = "failed"
                    delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                    await session.commit()
        except Exception as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)[:500]
            delivery.attempt = attempt
            await session.commit()

        return {"status": "failed", "delivery_id": delivery_id, "attempt": attempt}


