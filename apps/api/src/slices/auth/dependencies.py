import uuid
from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import ForbiddenException, UnauthorizedException
from src.core.security import decode_token
from src.slices.apikeys.dependencies import current_api_key_context
from src.slices.apikeys.service import authenticate_api_key
from src.slices.auth.models import User
from src.slices.auth.service import get_user_by_id


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    access_token_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User:
    """
    Extrai e valida as credenciais do usuário.
    Suporta:
    1. Chaves de API / PATs via header X-API-Key ou Bearer sf_live_... / sf_test_...
    2. JWT via header Authorization: Bearer <jwt>
    3. JWT via cookie HttpOnly 'access_token'
    """
    # 1. Checagem de Chaves de API (M2M / Agentes Externos)
    raw_api_key: str | None = None
    if x_api_key:
        raw_api_key = x_api_key.strip()
    elif authorization and authorization.lower().startswith("bearer sf_"):
        raw_api_key = authorization[7:].strip()

    if raw_api_key:
        api_key = await authenticate_api_key(session, raw_api_key)
        if not api_key:
            raise UnauthorizedException(message="Chave de API inválida, revogada ou expirada")
        current_api_key_context.set(api_key)
        return api_key.user

    current_api_key_context.set(None)

    # 2. Checagem de JWT (Sessão Web Interativa)
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif access_token_cookie:
        token = access_token_cookie

    if not token:
        raise UnauthorizedException(message="Autenticação necessária para acessar este recurso")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException(message="Tipo de token inválido")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException(message="Token inválido")
        user_id = uuid.UUID(user_id_str)
    except Exception as err:
        raise UnauthorizedException(message="Token expirado ou inválido") from err

    user = await get_user_by_id(session, user_id)
    if not user:
        raise UnauthorizedException(message="Usuário não encontrado")
    if not user.is_active:
        raise UnauthorizedException(message="Usuário inativo")

    return user



async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Garante que o usuário autenticado possui privilégios de superadministrador."""
    if not current_user.is_superuser:
        raise ForbiddenException(message="Requer privilégios de administrador")
    return current_user
