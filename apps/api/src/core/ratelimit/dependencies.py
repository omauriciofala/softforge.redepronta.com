from collections.abc import Callable
from typing import Literal

from fastapi import Request, Response

from src.core.errors import RateLimitExceededException
from src.core.ratelimit.limiter import get_rate_limiter
from src.slices.apikeys.dependencies import get_current_api_key


def get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente considerando cabeçalhos de proxy reverso."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def check_rate_limit(
    requests: int = 60,
    window_seconds: int = 60,
    by: Literal["ip", "user", "api_key", "auto"] = "auto",
    action: str = "default",
) -> Callable[..., object]:
    """
    Fábrica de dependências FastAPI para aplicar limitação de taxa (Rate Limiting).

    Insere automaticamente cabeçalhos RFC no response:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset

    Caso o limite seja excedido, lança RateLimitExceededException (HTTP 429) com Retry-After.
    """

    async def _rate_limiter_dependency(
        request: Request,
        response: Response,
    ) -> None:
        client_ip = get_client_ip(request)
        identifier = f"ip:{client_ip}"

        if by == "ip":
            identifier = f"ip:{client_ip}"
        elif by in ("auto", "api_key"):
            api_key = get_current_api_key()
            if api_key:
                identifier = f"apikey:{api_key.id}"
            elif by == "api_key":
                identifier = f"ip:{client_ip}"

        if by == "auto" and not identifier.startswith("apikey:"):
            # Verifica se há usuário no request state se autenticado anteriormente
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                identifier = f"user:{user_id}"

        rate_key = f"{action}:{identifier}"
        limiter = get_rate_limiter()
        res = await limiter.is_allowed(rate_key, limit=requests, window_seconds=window_seconds)

        # Injeta cabeçalhos no response
        response.headers["X-RateLimit-Limit"] = str(res.limit)
        response.headers["X-RateLimit-Remaining"] = str(res.remaining)
        response.headers["X-RateLimit-Reset"] = str(res.reset_time)

        if not res.allowed:
            raise RateLimitExceededException(
                message=(
                    f"Limite de requisições excedido ({requests} requisições a cada {window_seconds} segundos). "
                    f"Aguarde {res.retry_after} segundos antes de tentar novamente."
                ),
                retry_after=res.retry_after,
            )

    return _rate_limiter_dependency
