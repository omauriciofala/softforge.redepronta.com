from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from src.config import settings
from src.core.errors import AppException


@dataclass
class OAuthUserInfo:
    provider: str
    provider_user_id: str
    email: str
    full_name: str
    avatar_url: str | None = None


class BaseOAuthProvider:
    provider_name: str = ""

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        raise NotImplementedError

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        raise NotImplementedError


class GoogleOAuthProvider(BaseOAuthProvider):
    provider_name = "google"

    def __init__(self) -> None:
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.is_configured = bool(self.client_id and self.client_secret)

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id or "mock-google-client-id",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "select_account",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        # Mock offline para dev e testes locais
        if code.startswith("mock-") or not self.is_configured:
            clean_id = code.replace("mock-", "") or "user_123"
            return OAuthUserInfo(
                provider="google",
                provider_user_id=f"google_{clean_id}",
                email=f"user.{clean_id}@gmail.com",
                full_name=f"Google User {clean_id}",
                avatar_url=f"https://lh3.googleusercontent.com/a/{clean_id}",
            )

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise AppException("Falha ao trocar código de autorização com o Google.", status_code=400)

            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                raise AppException("Falha ao obter perfil do usuário no Google.", status_code=400)

            info: dict[str, Any] = user_resp.json()
            return OAuthUserInfo(
                provider="google",
                provider_user_id=str(info["id"]),
                email=info["email"],
                full_name=info.get("name") or info["email"].split("@")[0],
                avatar_url=info.get("picture"),
            )


class GitHubOAuthProvider(BaseOAuthProvider):
    provider_name = "github"

    def __init__(self) -> None:
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.is_configured = bool(self.client_id and self.client_secret)

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id or "mock-github-client-id",
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        # Mock offline para dev e testes locais
        if code.startswith("mock-") or not self.is_configured:
            clean_id = code.replace("mock-", "") or "user_123"
            return OAuthUserInfo(
                provider="github",
                provider_user_id=f"github_{clean_id}",
                email=f"user.{clean_id}@users.noreply.github.com",
                full_name=f"GitHub User {clean_id}",
                avatar_url=f"https://avatars.githubusercontent.com/u/{clean_id}",
            )

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                },
            )
            if token_resp.status_code != 200:
                raise AppException("Falha ao trocar código de autorização com o GitHub.", status_code=400)

            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            if user_resp.status_code != 200:
                raise AppException("Falha ao obter perfil do usuário no GitHub.", status_code=400)

            info: dict[str, Any] = user_resp.json()

            # Busca e-mail principal caso o perfil seja privado
            email = info.get("email")
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if emails_resp.status_code == 200:
                    emails = emails_resp.json()
                    primary = next((e for e in emails if e.get("primary")), None)
                    email = primary["email"] if primary else emails[0]["email"]

            return OAuthUserInfo(
                provider="github",
                provider_user_id=str(info["id"]),
                email=email or f"{info['login']}@users.noreply.github.com",
                full_name=info.get("name") or info["login"],
                avatar_url=info.get("avatar_url"),
            )


def get_oauth_provider(provider: str) -> BaseOAuthProvider:
    providers: dict[str, type[BaseOAuthProvider]] = {
        "google": GoogleOAuthProvider,
        "github": GitHubOAuthProvider,
    }
    provider_cls = providers.get(provider.lower())
    if not provider_cls:
        raise AppException(f"Provedor OAuth '{provider}' não suportado. Use 'google' ou 'github'.", status_code=400)
    return provider_cls()
