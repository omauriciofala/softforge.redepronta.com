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
