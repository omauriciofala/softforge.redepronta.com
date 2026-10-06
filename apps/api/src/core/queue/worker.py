from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron
from loguru import logger

from src.config import settings
from src.core.database import AsyncSessionLocal
from src.core.queue.tasks import (
    cleanup_revoked_tokens,
    process_subscription_renewal,
    send_transactional_email,
)


async def startup(ctx: dict[str, Any]) -> None:
    ctx["session_maker"] = AsyncSessionLocal
    logger.info("[Worker] Arq Background Worker iniciado com sucesso.")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("[Worker] Arq Background Worker finalizado.")


class WorkerSettings:
    """Configurações do processo Worker do Arq (executado via 'arq src.core.queue.worker.WorkerSettings')."""

    functions = [
        send_transactional_email,
        process_subscription_renewal,
        cleanup_revoked_tokens,
    ]

    # Tarefa cron diária às 03:00 UTC para limpeza de tokens revogados
    cron_jobs = [
        cron(cleanup_revoked_tokens, hour=3, minute=0),
    ]

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    burst = settings.WORKER_BURST
    max_jobs = 10
    job_timeout = 300  # 5 minutos por job
