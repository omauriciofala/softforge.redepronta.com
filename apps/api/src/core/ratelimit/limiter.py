import asyncio
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from loguru import logger
from redis.asyncio import Redis

from src.config import settings


@dataclass
class RateLimitResult:
    """Resultado da checagem de cota de requisições."""

    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: int


class BaseRateLimiter:
    """Interface abstrata para limitadores de taxa."""

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        raise NotImplementedError

    def clear(self) -> None:
        pass


class MemoryRateLimiter(BaseRateLimiter):
    """
    Limitador Sliding Window em memória com alto desempenho (sub-milissegundo).
    Utilizado para testes automatizados offline e desenvolvimento local.
    """

    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            timestamps = self._windows[key]

            # Remove timestamps fora da janela deslizante
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            count = len(timestamps)

            if count >= limit:
                oldest = timestamps[0]
                reset_time = int(oldest + window_seconds)
                retry_after = max(1, int(reset_time - now))
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after,
                )

            # Registra a requisição atual
            timestamps.append(now)
            remaining = limit - (count + 1)
            reset_time = int(now + window_seconds)

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=0,
            )

    def clear(self) -> None:
        self._windows.clear()


class RedisRateLimiter(BaseRateLimiter):
    """
    Limitador Sliding Window distribuído baseado em Redis Sorted Sets (ZSET).
    Executa atomicamente ZREMRANGEBYSCORE, ZCARD e ZADD com expiração automática.
    """

    def __init__(self, redis_client: Redis, fallback: MemoryRateLimiter) -> None:
        self.redis = redis_client
        self.fallback = fallback

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        try:
            now = time.time()
            cutoff = now - window_seconds
            redis_key = f"rl:{key}"

            async with self.redis.pipeline(transaction=True) as pipe:
                # 1. Remove requisições expiradas
                pipe.zremrangebyscore(redis_key, 0, cutoff)
                # 2. Conta quantas requisições restam na janela
                pipe.zcard(redis_key)
                # 3. Busca a mais antiga para calcular reset_time
                pipe.zrange(redis_key, 0, 0, withscores=True)
                results: list[Any] = await pipe.execute()

            count = results[1]
            oldest_entries = results[2]

            if count >= limit:
                oldest_score = oldest_entries[0][1] if oldest_entries else now
                reset_time = int(oldest_score + window_seconds)
                retry_after = max(1, int(reset_time - now))
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after,
                )

            # Adiciona a requisição atual e define TTL na chave
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, window_seconds + 5)
                await pipe.execute()

            remaining = limit - (count + 1)
            reset_time = int(now + window_seconds)

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=0,
            )
        except Exception as exc:
            logger.warning(
                f"[RateLimit] Falha ao comunicar com Redis ({exc}). Ativando fallback em memória."
            )
            return await self.fallback.is_allowed(key, limit, window_seconds)

    def clear(self) -> None:
        self.fallback.clear()


# Singletons
_memory_limiter = MemoryRateLimiter()
_rate_limiter: BaseRateLimiter | None = None


def get_rate_limiter() -> BaseRateLimiter:
    """Retorna o limitador ativo (MemoryLimiter para dev/testes ou Redis em produção)."""
    global _rate_limiter

    # Se estiver rodando pytest ou sem Redis ativo, usa o limitador em memória
    if os.environ.get("TESTING") == "true" or settings.ENVIRONMENT == "development":
        return _memory_limiter

    if _rate_limiter is None:
        try:
            redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
            _rate_limiter = RedisRateLimiter(redis_client, fallback=_memory_limiter)
        except Exception:
            _rate_limiter = _memory_limiter

    return _rate_limiter
