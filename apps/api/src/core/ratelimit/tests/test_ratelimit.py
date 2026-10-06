import pytest
from httpx import AsyncClient

from src.core.ratelimit.limiter import MemoryRateLimiter, get_rate_limiter


@pytest.mark.asyncio
async def test_memory_rate_limiter_unit_sliding_window() -> None:
    """Valida a mecânica de contagem e bloqueio por janela deslizante da MemoryRateLimiter."""
    limiter = MemoryRateLimiter()
    key = "unit_test_key"

    # Permite 3 requisições
    r1 = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert r1.allowed is True
    assert r1.remaining == 2
    assert r1.limit == 3

    r2 = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert r2.allowed is True
    assert r2.remaining == 1

    r3 = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert r3.allowed is True
    assert r3.remaining == 0

    # 4ª requisição deve ser bloqueada
    r4 = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert r4.allowed is False
    assert r4.remaining == 0
    assert r4.retry_after >= 1

    # Chave diferente não deve ser afetada
    other = await limiter.is_allowed("other_key", limit=3, window_seconds=10)
    assert other.allowed is True
    assert other.remaining == 2


@pytest.mark.asyncio
async def test_rate_limit_headers_and_system_status(client: AsyncClient) -> None:
    """Valida inserção de cabeçalhos RFC e endpoint de consulta de cota para agentes."""
    resp = await client.get("/api/v1/system/rate-limit")
    assert resp.status_code == 200

    # Valida cabeçalhos obrigatórios
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers
    assert "X-RateLimit-Reset" in resp.headers

    limit = int(resp.headers["X-RateLimit-Limit"])
    remaining = int(resp.headers["X-RateLimit-Remaining"])
    assert limit >= 1
    assert remaining >= 0

    data = resp.json()
    assert data["status"] == "active"
    assert "client_ip" in data
    assert data["limit"] == limit


@pytest.mark.asyncio
async def test_rate_limit_exceeded_returns_http_429(client: AsyncClient) -> None:
    """Simula saturação da cota de requisições e valida retorno do código HTTP 429 Too Many Requests."""
    limiter = get_rate_limiter()
    # Registra artificialmente requisições na chave para atingir o limite
    test_key = "auth_login:ip:127.0.0.1"

    # Preenche a cota do login (limite de 60)
    for _ in range(60):
        await limiter.is_allowed(test_key, limit=60, window_seconds=60)

    # Requisição subsequente no login deve ser barrada pelo middleware
    blocked_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "WrongPassword123!"},
    )
    assert blocked_resp.status_code == 429
    assert blocked_resp.json()["error"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in blocked_resp.headers
    assert int(blocked_resp.headers["Retry-After"]) >= 1

    # Limpa o limiter para não poluir testes posteriores
    limiter.clear()
