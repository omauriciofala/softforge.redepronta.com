import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.errors import NotFoundException
from src.slices.apikeys.models import ApiKey
from src.slices.apikeys.schemas import ApiKeyCreate
from src.slices.apikeys.security import generate_api_key, hash_api_key


async def create_api_key(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    req: ApiKeyCreate,
) -> tuple[ApiKey, str]:
    """Cria uma nova chave de API criptograficamente protegida para o workspace."""
    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=req.expires_in_days)

    raw_key, key_prefix, hashed_key = generate_api_key(prefix="sf_live_")

    api_key = ApiKey(
        workspace_id=workspace_id,
        user_id=user_id,
        name=req.name,
        key_prefix=key_prefix,
        hashed_key=hashed_key,
        scopes=req.scopes or ["*"],
        expires_at=expires_at,
        is_revoked=False,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key, raw_key


async def list_api_keys(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[ApiKey]:
    """Lista todas as chaves de API registradas para o workspace."""
    stmt = (
        select(ApiKey)
        .where(ApiKey.workspace_id == workspace_id)
        .order_by(ApiKey.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_api_keys(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> int:
    """Retorna o total de chaves cadastradas no workspace."""
    stmt = (
        select(func.count(ApiKey.id))
        .where(ApiKey.workspace_id == workspace_id)
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_api_key_by_id(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
) -> ApiKey:
    """Obtém os dados de uma chave de API específica validando o workspace."""
    stmt = select(ApiKey).where(
        ApiKey.id == key_id,
        ApiKey.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise NotFoundException(message="Chave de API não encontrada.")
    return api_key


async def revoke_api_key(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
) -> ApiKey:
    """Revoga imediatamente uma chave de API tornando-a inutilizável."""
    api_key = await get_api_key_by_id(session, workspace_id, key_id)
    if api_key.is_revoked:
        return api_key

    api_key.is_revoked = True
    api_key.revoked_at = datetime.now(UTC)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key


async def authenticate_api_key(
    session: AsyncSession,
    raw_key: str,
) -> ApiKey | None:
    """
    Verifica a autenticidade da chave bruta recebida.

    Retorna a instância de ApiKey vinculada ao usuário caso válida, ou None se:
    - O hash não existir no banco
    - A chave estiver revogada
    - A chave estiver expirada
    - O usuário proprietário estiver inativo
    """
    hashed = hash_api_key(raw_key)

    stmt = (
        select(ApiKey)
        .options(joinedload(ApiKey.user))
        .where(
            ApiKey.hashed_key == hashed,
            ApiKey.is_revoked.is_(False),
        )
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        return None

    # Valida expiração
    if api_key.expires_at:
        now_utc = datetime.now(UTC)
        # Normaliza timezone se necessário
        exp = api_key.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < now_utc:
            return None

    # Valida se usuário criador está ativo
    if not api_key.user or not api_key.user.is_active:
        return None

    # Registra uso mais recente
    api_key.last_used_at = datetime.now(UTC)
    session.add(api_key)
    await session.commit()

    return api_key
