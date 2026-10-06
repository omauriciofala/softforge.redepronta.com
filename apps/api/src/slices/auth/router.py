from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.database import get_db
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.auth.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from src.slices.auth.service import (
    authenticate_user,
    create_tokens_for_user,
    create_user,
    refresh_tokens,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    is_secure = settings.is_production
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cria uma nova conta de usuário no sistema.",
)
async def register(
    req: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await create_user(session, req)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário",
    description="Valida e-mail e senha, retornando tokens JWT e gravando cookies HttpOnly.",
)
async def login(
    req: UserLoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await authenticate_user(session, req)
    tokens = await create_tokens_for_user(session, user)
    _set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar token de acesso",
    description="Emite um novo par de tokens a partir de um refresh token válido.",
)
async def refresh(
    req: RefreshTokenRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    tokens = await refresh_tokens(session, req.refresh_token)
    _set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Encerrar sessão",
    description="Limpa os cookies de autenticação do navegador.",
)
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Sessão encerrada com sucesso"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter dados do usuário autenticado",
    description="Retorna os detalhes do usuário logado atualmente.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
