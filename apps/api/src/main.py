from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.database import engine
from src.core.errors import register_exception_handlers
from src.core.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, get_translations_catalog, t
from src.core.logging import logger, setup_logging
from src.core.middleware import RequestContextMiddleware
from src.core.queue import close_queue_pool, init_queue_pool
from src.core.ratelimit import check_rate_limit, get_client_ip
from src.slices.apikeys.router import router as apikeys_router
from src.slices.audit.router import router as audit_router
from src.slices.auth.router import router as auth_router
from src.slices.billing.router import router as billing_router
from src.slices.dev_tasks.router import router as dev_tasks_router
from src.slices.feature_flags.router import router as feature_flags_router
from src.slices.notifications.router import router as notifications_router
from src.slices.projects.router import router as projects_router
from src.slices.storage.router import router as storage_router
from src.slices.themes.router import router as themes_router
from src.slices.webhooks.router import router as webhooks_router
from src.slices.workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    setup_logging()
    logger.info(
        f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} no ambiente '{settings.ENVIRONMENT}'"
    )
    if "sqlite" in settings.DATABASE_URL:
        from src.core.database import Base, discover_and_import_models
        discover_and_import_models()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[Database] Banco SQLite inicializado automaticamente com todas as tabelas.")
    await init_queue_pool()
    yield
    logger.info("Encerrando conexões com fila e banco de dados...")
    await close_queue_pool()
    await engine.dispose()
    logger.info("Servidor finalizado com sucesso.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="SoftForge API — Framework Fullstack AI-Native construído sobre Vertical Slice Architecture.",
    lifespan=lifespan,
)

# Registra handlers de erro e middleware de correlação
register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Roteadores das Fatias Verticais
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(workspaces_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(billing_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)
app.include_router(apikeys_router, prefix=settings.API_V1_STR)
app.include_router(storage_router, prefix=settings.API_V1_STR)
app.include_router(feature_flags_router, prefix=settings.API_V1_STR)
app.include_router(themes_router, prefix=settings.API_V1_STR)
app.include_router(dev_tasks_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Sistema"])
async def healthcheck() -> dict[str, Any]:
    """Endpoint de checagem de saúde e vitalidade da API."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get(
    f"{settings.API_V1_STR}/system/rate-limit",
    tags=["Sistema"],
    summary="Consultar cota de rate limit",
    description="Permite que clientes e agentes autônomos de IA consultem sua cota de requisições e IP detectado.",
    dependencies=[Depends(check_rate_limit(requests=60, window_seconds=60, by="auto", action="system_quota"))],
)
async def get_rate_limit_status(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    client_ip = get_client_ip(request)
    return {
        "status": "active",
        "client_ip": client_ip,
        "limit": int(response.headers.get("X-RateLimit-Limit", "60")),
        "remaining": int(response.headers.get("X-RateLimit-Remaining", "59")),
        "reset_time": int(response.headers.get("X-RateLimit-Reset", "0")),
    }


@app.get(
    f"{settings.API_V1_STR}/system/i18n",
    tags=["Sistema"],
    summary="Consultar status de internacionalização (i18n)",
    description="Informa o idioma detectado da requisição, idiomas suportados pelo framework e mensagens traduzidas.",
)
async def get_i18n_status(request: Request) -> dict[str, Any]:
    locale = getattr(request.state, "locale", DEFAULT_LOCALE)
    return {
        "current_locale": locale,
        "default_locale": DEFAULT_LOCALE,
        "supported_locales": list(SUPPORTED_LOCALES),
        "welcome_message": t("system.welcome", locale=locale),
        "translations_count": len(get_translations_catalog(locale)),
    }

