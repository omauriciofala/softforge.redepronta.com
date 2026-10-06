import os
import uuid
from typing import Any

from arq.connections import ArqRedis, RedisSettings, create_pool
from loguru import logger

from src.config import settings


class FakeJob:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id


class FakeQueueClient:
    """Fila assíncrona em memória para testes e desenvolvimento 100% offline."""

    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []

    async def enqueue(self, function_name: str, *args: Any, **kwargs: Any) -> str:
        job_id = f"fake-job-{uuid.uuid4().hex[:8]}"
        job_record = {
            "job_id": job_id,
            "function": function_name,
            "args": args,
            "kwargs": kwargs,
        }
        self.jobs.append(job_record)
        logger.debug(
            f"[FakeQueue] Job enfileirado em memória: {function_name} [id={job_id}, args={args}, kwargs={kwargs}]"
        )
        return job_id

    def clear(self) -> None:
        self.jobs.clear()

    @property
    def enqueued_count(self) -> int:
        return len(self.jobs)


class ArqQueueClient:
    """Cliente de fila assíncrona Arq conectado ao Redis."""

    def __init__(self, pool: ArqRedis) -> None:
        self.pool = pool

    async def enqueue(self, function_name: str, *args: Any, **kwargs: Any) -> str | None:
        job = await self.pool.enqueue_job(function_name, *args, **kwargs)
        if job:
            logger.info(f"[ArqQueue] Job enfileirado no Redis: {function_name} [id={job.job_id}]")
            return job.job_id
        return None


# Instância global reutilizável para pool e fake queue
_redis_pool: ArqRedis | None = None
_fake_queue: FakeQueueClient = FakeQueueClient()


async def init_queue_pool() -> ArqRedis | FakeQueueClient:
    """Inicializa o pool de conexões Redis para o Arq com fallback offline para FakeQueue."""
    global _redis_pool

    # Em ambiente de teste ou se marcado explicitamente como offline
    is_test_env = (
        settings.ENVIRONMENT == "development" and os.environ.get("PYTEST_CURRENT_TEST") is not None
    ) or os.environ.get("TESTING") == "1"

    if is_test_env:
        logger.debug("[Queue] Modo de teste detectado: usando FakeQueueClient em memória.")
        return _fake_queue

    try:
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        _redis_pool = await create_pool(redis_settings)
        logger.info(f"[Queue] Conectado com sucesso ao Redis ({settings.REDIS_URL})")
        return ArqQueueClient(_redis_pool)
    except Exception as exc:
        logger.warning(
            f"[Queue] Não foi possível conectar ao Redis ({exc}). Ativando FakeQueueClient offline."
        )
        return _fake_queue


async def close_queue_pool() -> None:
    """Encerra com segurança o pool de conexões do Redis."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("[Queue] Pool do Redis fechado.")


async def get_queue() -> ArqQueueClient | FakeQueueClient:
    """Dependência injetável do FastAPI para enfileiramento de jobs."""
    global _redis_pool
    is_test_env = (
        settings.ENVIRONMENT == "development" and os.environ.get("PYTEST_CURRENT_TEST") is not None
    ) or os.environ.get("TESTING") == "1"

    if is_test_env:
        return _fake_queue

    if _redis_pool is not None:
        return ArqQueueClient(_redis_pool)

    # Tenta inicializar se ainda não estiver pronto
    return await init_queue_pool()


def get_fake_queue() -> FakeQueueClient:
    """Retorna a instância do FakeQueue para inspeção em asserções de testes."""
    return _fake_queue
