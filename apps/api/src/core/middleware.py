import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware responsável por:
    1. Injetar um Request ID único (Correlation ID) em toda requisição e resposta.
    2. Calcular o tempo de processamento da requisição (X-Process-Time).
    3. Registrar log estruturado de cada chamada HTTP com status e duração.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.debug(f"HTTP {request.method} {request.url.path} iniciado [request_id={request_id}]")

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"HTTP {request.method} {request.url.path} falhou após {duration_ms:.2f}ms: {exc} [request_id={request_id}]"
            )
            raise exc

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        log_level = "info" if response.status_code < 400 else "warning"
        getattr(logger, log_level)(
            f"HTTP {request.method} {request.url.path} concluído com {response.status_code} "
            f"em {duration_ms:.2f}ms [request_id={request_id}]"
        )

        return response
