import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from src.config import settings
from src.core.database import Base, discover_and_import_models

# Carrega e interpreta o arquivo de log do Alembic se existir
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Descobre e importa dinamicamente todos os models das fatias verticais
discover_and_import_models()

# Define o metadata alvo do SQLAlchemy 2.0
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline' (emite SQL diretamente sem conexão ativa)."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executa as operações de migração na conexão fornecida."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria um AsyncEngine conectado ao PostgreSQL e aplica as migrações."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Ponto de entrada para migrações no modo online (assíncrono)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
