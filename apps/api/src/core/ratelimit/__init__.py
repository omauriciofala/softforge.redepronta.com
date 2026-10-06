"""Módulo de Rate Limiting e Proteção Contra Abuso do SoftForge."""

from src.core.ratelimit.dependencies import check_rate_limit, get_client_ip
from src.core.ratelimit.limiter import (
    BaseRateLimiter,
    MemoryRateLimiter,
    RateLimitResult,
    RedisRateLimiter,
    get_rate_limiter,
)

__all__ = [
    "check_rate_limit",
    "get_client_ip",
    "BaseRateLimiter",
    "MemoryRateLimiter",
    "RedisRateLimiter",
    "RateLimitResult",
    "get_rate_limiter",
]
