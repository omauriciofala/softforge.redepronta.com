import importlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import settings

# Convenção de nomenclatura de constraints padrão para Alembic e PostgreSQL
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

# Engine assíncrono para PostgreSQL (e SQLite durante testes)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and not settings.is_production,
    future=True,
    pool_pre_ping=True,
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy 2.0 com campos auditáveis padrão."""

    metadata = metadata

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


def discover_and_import_models() -> None:
    """Escaneia dinamicamente e importa todos os models.py das fatias verticais.

    Permite que o Alembic (env.py) e a suíte de testes (conftest.py) reconheçam
    todas as tabelas do Base.metadata sem necessidade de imports manuais.
    """
    slices_dir = Path(__file__).resolve().parent.parent / "slices"
    if not slices_dir.exists():
        return
    for item in slices_dir.iterdir():
        if item.is_dir() and (item / "models.py").exists():
            module_name = f"src.slices.{item.name}.models"
            importlib.import_module(module_name)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Dependência FastAPI que injeta uma sessão do banco com rollback automático em erros."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
