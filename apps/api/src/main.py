from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.database import engine
from src.core.errors import register_exception_handlers
from src.core.logging import logger, setup_logging
from src.core.middleware import RequestContextMiddleware
from src.core.queue import close_queue_pool, init_queue_pool
from src.slices.apikeys.router import router as apikeys_router
from src.slices.audit.router import router as audit_router
from src.slices.auth.router import router as auth_router
from src.slices.billing.router import router as billing_router
from src.slices.notifications.router import router as notifications_router
from src.slices.projects.router import router as projects_router
from src.slices.storage.router import router as storage_router
from src.slices.webhooks.router import router as webhooks_router
from src.slices.workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    setup_logging()
    logger.info(
        f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} no ambiente '{settings.ENVIRONMENT}'"
    )
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
