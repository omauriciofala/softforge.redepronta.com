from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logging import logger


class AppException(Exception):
    """Exceção base para erros de domínio de negócio no SoftForge."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers or {}
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso não encontrado", details: Any = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Não autenticado", details: Any = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenException(AppException):
    def __init__(
        self, message: str = "Acesso negado para esta operação", details: Any = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            details=details,
        )


class RateLimitExceededException(AppException):
    def __init__(
        self,
        message: str = "Limite de requisições excedido. Tente novamente mais tarde.",
        retry_after: int = 60,
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            details=details,
            headers={"Retry-After": str(retry_after)},
        )
        self.retry_after = retry_after


def register_exception_handlers(app: FastAPI) -> None:
    """Registra manipuladores de exceções globais para respostas JSON padronizadas."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(f"Erro de validação na requisição: {exc.errors()} [request_id={request_id}]")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Dados de requisição inválidos",
                "details": exc.errors(),
                "request_id": request_id,
            },
        )
