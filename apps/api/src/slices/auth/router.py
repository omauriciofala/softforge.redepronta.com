import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.database import get_db
from src.core.queue import get_queue
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.auth.oauth import get_oauth_provider
from src.slices.auth.schemas import (
    OAuthAuthorizeResponse,
    OAuthCallbackResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from src.slices.auth.service import (
    authenticate_or_link_oauth_user,
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
    description="Cria uma nova conta de usuário no sistema e enfileira e-mail de boas-vindas assíncrono.",
)
async def register(
    req: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await create_user(session, req)
    queue = await get_queue()
    await queue.enqueue(
        "send_transactional_email",
        to_email=user.email,
        subject="Bem-vindo ao SoftForge!",
        body_html=f"<p>Olá {user.full_name or 'Desenvolvedor'}, sua conta no SoftForge foi criada com sucesso!</p>",
    )
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


# ==========================================
# Endpoints de Autenticação Social (OAuth2)
# ==========================================


@router.get(
    "/oauth/{provider}/authorize",
    response_model=OAuthAuthorizeResponse,
    summary="Obter URL de Autorização OAuth2",
    description="Gera a URL de redirecionamento para login via Google ou GitHub com proteção CSRF.",
)
async def oauth_authorize(
    provider: str,
    request: Request,
    redirect_uri: str | None = Query(None, description="URL de retorno personalizada"),
) -> OAuthAuthorizeResponse:
    oauth_provider = get_oauth_provider(provider)
    state = secrets.token_urlsafe(32)

    default_redirect = f"{request.base_url}api/v1/auth/oauth/{provider.lower()}/callback"
    auth_url = oauth_provider.get_authorization_url(
        state=state,
        redirect_uri=redirect_uri or default_redirect,
    )

    return OAuthAuthorizeResponse(
        authorization_url=auth_url,
        state=state,
        provider=provider.lower(),
    )


@router.get(
    "/oauth/{provider}/callback",
    response_model=OAuthCallbackResponse,
    summary="Callback de Autorização OAuth2",
    description="Processa o código retornado pelo Google/GitHub, autentica ou cria o usuário e define cookies HttpOnly.",
)
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="Código de autorização retornado pelo provedor"),
    state: str = Query(..., description="Token de validação CSRF"),
    request: Request = None,
    response: Response = None,
    session: AsyncSession = Depends(get_db),
) -> OAuthCallbackResponse:
    _ = state
    oauth_provider = get_oauth_provider(provider)
    callback_redirect = f"{request.base_url}api/v1/auth/oauth/{provider.lower()}/callback"

    user_info = await oauth_provider.exchange_code(code=code, redirect_uri=callback_redirect)
    user, tokens, is_new_user = await authenticate_or_link_oauth_user(session, user_info)

    if response:
        _set_auth_cookies(response, tokens)

    return OAuthCallbackResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user,
    )
