from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.i18n.translator import get_current_locale, t
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
        message_key: str | None = None,
        message_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers or {}
        self.message_key = message_key
        self.message_kwargs = message_kwargs or {}
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Recurso não encontrado",
        details: Any = None,
        message_key: str | None = None,
        message_kwargs: dict[str, Any] | None = None,
    ) -> None:
        key = message_key or ("errors.not_found" if message == "Recurso não encontrado" else None)
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details=details,
            message_key=key,
            message_kwargs=message_kwargs,
        )


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Não autenticado",
        details: Any = None,
        message_key: str | None = None,
        message_kwargs: dict[str, Any] | None = None,
    ) -> None:
        key = message_key or ("errors.unauthorized" if message == "Não autenticado" else None)
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            details=details,
            message_key=key,
            message_kwargs=message_kwargs,
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Acesso negado para esta operação",
        details: Any = None,
        message_key: str | None = None,
        message_kwargs: dict[str, Any] | None = None,
    ) -> None:
        key = message_key or ("errors.forbidden" if message == "Acesso negado para esta operação" else None)
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            details=details,
            message_key=key,
            message_kwargs=message_kwargs,
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


class FeatureFlagDisabledException(AppException):
    def __init__(
        self,
        flag_key: str,
        message: str | None = None,
        details: Any = None,
    ) -> None:
        msg = message or f"A funcionalidade '{flag_key}' está desabilitada para este workspace."
        super().__init__(
            message=msg,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FEATURE_FLAG_DISABLED",
            details=details or {"flag_key": flag_key},
        )
        self.flag_key = flag_key


def register_exception_handlers(app: FastAPI) -> None:
    """Registra manipuladores de exceções globais para respostas JSON padronizadas com suporte a i18n."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        locale = getattr(request.state, "locale", None) or get_current_locale()

        # Tradução dinâmica conforme chave explícita ou mapeamento de erros padrão
        message = exc.message
        if exc.message_key:
            message = t(exc.message_key, locale=locale, **exc.message_kwargs)
        elif exc.code == "NOT_FOUND" and exc.message == "Recurso não encontrado":
            message = t("errors.not_found", locale=locale)
        elif exc.code == "UNAUTHORIZED" and exc.message == "Não autenticado":
            message = t("errors.unauthorized", locale=locale)
        elif exc.code == "FORBIDDEN" and exc.message == "Acesso negado para esta operação":
            message = t("errors.forbidden", locale=locale)
        elif exc.code == "RATE_LIMIT_EXCEEDED" and hasattr(exc, "retry_after"):
            message = t("errors.rate_limit_exceeded", locale=locale, retry_after=exc.retry_after)
        elif exc.code == "FEATURE_FLAG_DISABLED" and hasattr(exc, "flag_key"):
            message = t("errors.feature_flag_disabled", locale=locale, flag_key=exc.flag_key)

        response_headers = dict(exc.headers)
        if "Content-Language" not in response_headers:
            response_headers["Content-Language"] = locale
        if request_id and "X-Request-ID" not in response_headers:
            response_headers["X-Request-ID"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.code,
                "message": message,
                "details": exc.details,
                "request_id": request_id,
            },
            headers=response_headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        locale = getattr(request.state, "locale", None) or get_current_locale()
        logger.warning(f"Erro de validação na requisição: {exc.errors()} [request_id={request_id}]")

        msg = (
            "Dados de requisição inválidos"
            if locale == "pt-BR"
            else "Invalid request data"
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": msg,
                "details": exc.errors(),
                "request_id": request_id,
            },
            headers={
                "Content-Language": locale,
                **({"X-Request-ID": request_id} if request_id else {}),
            },
        )
