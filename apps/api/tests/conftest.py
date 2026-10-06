from collections.abc import AsyncGenerator
from typing import Any
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.database import Base, get_db
from src.main import app

# Importa todos os models para que o Base.metadata reconheça todas as tabelas
import src.slices.auth.models  # noqa: F401
import src.slices.projects.models  # noqa: F401
import src.slices.workspaces.models  # noqa: F401

# Banco de dados SQLite in-memory para testes assíncronos ultrarrápidos e isolados
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, Any]:
    """Cria o schema completo do banco em memória antes dos testes e destrói após a execução."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, Any]:
    """Fornece uma sessão isolada para cada teste."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, Any]:
    """Cliente HTTP assíncrono conectado à aplicação FastAPI com banco mockado."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, Any]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
