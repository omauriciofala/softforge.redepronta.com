from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient) -> None:
    # 1. Registro
    reg_payload = {
        "email": "developer@softforge.com",
        "password": "SuperSecretPassword123!",
        "full_name": "Agente AI Developer",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()
    assert user_data["email"] == "developer@softforge.com"
    assert user_data["full_name"] == "Agente AI Developer"
    assert "id" in user_data

    # 2. Login com sucesso
    login_payload = {
        "email": "developer@softforge.com",
        "password": "SuperSecretPassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200, login_res.text
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Consulta ao /me com o Bearer token
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_data["id"]
    assert me_data["email"] == "developer@softforge.com"

    # 4. Login com senha errada
    bad_login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "developer@softforge.com", "password": "WrongPassword!"},
    )
    assert bad_login_res.status_code == 401


@pytest.mark.asyncio
async def test_oauth_authorize_urls(client: AsyncClient) -> None:
    """Verifica a geração de URLs de autorização com state CSRF para Google e GitHub."""
    # Google
    google_resp = await client.get("/api/v1/auth/oauth/google/authorize")
    assert google_resp.status_code == 200
    google_data = google_resp.json()
    assert "accounts.google.com" in google_data["authorization_url"]
    assert google_data["provider"] == "google"
    assert len(google_data["state"]) > 10

    # GitHub
    github_resp = await client.get("/api/v1/auth/oauth/github/authorize")
    assert github_resp.status_code == 200
    github_data = github_resp.json()
    assert "github.com/login/oauth/authorize" in github_data["authorization_url"]
    assert github_data["provider"] == "github"
    assert len(github_data["state"]) > 10


@pytest.mark.asyncio
async def test_oauth_callback_and_account_linking(client: AsyncClient) -> None:
    """Verifica criação de novo usuário social e auto-linking quando o e-mail já existe."""
    # 1. Login social criando novo usuário via Google
    cb_resp = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "mock-google-user99", "state": "test_csrf_state"},
    )
    assert cb_resp.status_code == 200
    cb_data = cb_resp.json()
    assert cb_data["is_new_user"] is True
    assert "access_token" in cb_data
    assert cb_data["user"]["email"] == "user.google-user99@gmail.com"

    # Valida consulta /me com o token gerado
    headers = {"Authorization": f"Bearer {cb_data['access_token']}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == cb_data["user"]["id"]

    # 2. Cadastro prévio manual via e-mail e senha
    existing_email = "preexisting@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": existing_email, "password": "Password123!", "full_name": "Usuário Existente"},
    )

    # 3. Usuário faz login social com o mesmo e-mail (usando mock com esse e-mail)
    from src.slices.auth.oauth import GoogleOAuthProvider, OAuthUserInfo

    async def mock_exchange(self: Any, code: str, redirect_uri: str) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider="google",
            provider_user_id="google_existing_link_123",
            email=existing_email,
            full_name="Usuário Existente",
            avatar_url="https://lh3.googleusercontent.com/avatar.png",
        )

    # Sobrescreve o método exchange temporariamente para simular o mesmo e-mail
    original_exchange = GoogleOAuthProvider.exchange_code
    GoogleOAuthProvider.exchange_code = mock_exchange  # type: ignore

    try:
        link_resp = await client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "custom-link-code", "state": "test_state"},
        )
        assert link_resp.status_code == 200
        link_data = link_resp.json()
        assert link_data["is_new_user"] is False  # Vinculou à conta existente!
        assert link_data["user"]["email"] == existing_email
    finally:
        GoogleOAuthProvider.exchange_code = original_exchange  # type: ignore
