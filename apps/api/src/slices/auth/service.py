import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, UnauthorizedException
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.slices.auth.models import RefreshToken, User
from src.slices.auth.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, req: UserRegisterRequest) -> User:
    existing = await get_user_by_email(session, req.email)
    if existing:
        raise AppException(
            message=f"O e-mail '{req.email}' já está registrado na plataforma.",
            status_code=409,
            code="EMAIL_ALREADY_EXISTS",
        )

    user = User(
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    return user


async def authenticate_user(session: AsyncSession, req: UserLoginRequest) -> User:
    user = await get_user_by_email(session, req.email)
    if not user:
        raise UnauthorizedException(message="Credenciais de acesso inválidas")

    if not verify_password(req.password, user.hashed_password):
        raise UnauthorizedException(message="Credenciais de acesso inválidas")

    if not user.is_active:
        raise UnauthorizedException(message="Esta conta de usuário está desativada")

    return user


async def create_tokens_for_user(session: AsyncSession, user: User) -> TokenResponse:
    payload = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    # Registra o hash do refresh token no banco para permitir revogação
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(UTC),  # Validado pelo JWT payload
        revoked=False,
    )
    session.add(token_record)
    await session.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def refresh_tokens(session: AsyncSession, refresh_token_str: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(message="Token inválido para renovação de sessão")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException(message="Payload de token inválido")
        user_id = uuid.UUID(user_id_str)
    except Exception as err:
        raise UnauthorizedException(message="Token de refresh expirado ou corrompido") from err

    # Verifica no banco se o token foi revogado
    token_hash = _hash_token(refresh_token_str)
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise UnauthorizedException(message="Sessão revogada ou inválida")

    # Marca o token anterior como revogado (rotatividade de refresh token)
    token_record.revoked = True

    user = await get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(message="Usuário inexistente ou inativo")

    return await create_tokens_for_user(session, user)
