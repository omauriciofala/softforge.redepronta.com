import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from conftest import TestingSessionLocal
from src.slices.apikeys.models import ApiKey
from src.slices.apikeys.security import (
    generate_api_key,
    has_required_scope,
    hash_api_key,
)


def test_api_key_generation_and_hashing() -> None:
    """Valida geração segura de tokens, hashes SHA-256 e verificação de escopos com curinga."""
    raw_key, prefix, hashed = generate_api_key(prefix="sf_live_")

    assert raw_key.startswith("sf_live_")
    assert "..." in prefix
    assert len(hashed) == 64
    assert hash_api_key(raw_key) == hashed

    # Testes de Escopo
    assert has_required_scope(["*"], "qualquer:coisa") is True
    assert has_required_scope(["projects:read"], "projects:read") is True
    assert has_required_scope(["projects:read"], "projects:write") is False
    assert has_required_scope(["projects:*"], "projects:create") is True
    assert has_required_scope(["projects:*"], "projects:delete") is True
    assert has_required_scope(["projects:*"], "billing:read") is False


@pytest.mark.asyncio
async def test_api_key_crud_lifecycle(client: AsyncClient) -> None:
    """Valida fluxo de criação, listagem com prefixos mascarados e revogação de chaves."""
    # 1. Registro e autenticação do usuário administrador
    owner_email = f"key_admin_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "Password123!", "full_name": "Key Admin"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    jwt_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Criação de Workspace
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Keys Workspace", "slug": f"keys-ws-{uuid.uuid4().hex[:6]}"},
        headers=jwt_headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 3. Criação de Chave de API
    create_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/api-keys",
        json={
            "name": "Cursor Assistant Agent",
            "scopes": ["projects:*"],
            "expires_in_days": 30,
        },
        headers=jwt_headers,
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert "raw_key" in created_data
    assert created_data["raw_key"].startswith("sf_live_")
    assert created_data["name"] == "Cursor Assistant Agent"
    assert created_data["is_revoked"] is False
    key_id = created_data["id"]

    # 4. Listagem de Chaves (nunca deve expor raw_key)
    list_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/api-keys",
        headers=jwt_headers,
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    found_key = next(k for k in list_data["items"] if k["id"] == key_id)
    assert "raw_key" not in found_key
    assert "..." in found_key["key_prefix"]

    # 5. Revogação de Chave
    revoke_resp = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/api-keys/{key_id}",
        headers=jwt_headers,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_revoked"] is True
    assert revoke_resp.json()["revoked_at"] is not None


@pytest.mark.asyncio
async def test_api_key_authentication_and_tenant_isolation(client: AsyncClient) -> None:
    """Valida autenticação M2M via X-API-Key e Bearer token, além do isolamento de workspace."""
    # 1. Registro e criação de dois workspaces
    email = f"agent_owner_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Agent Owner"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    jwt_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws1_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Workspace 1", "slug": f"ws1-{uuid.uuid4().hex[:6]}"},
        headers=jwt_headers,
    )
    ws1_id = ws1_resp.json()["id"]

    ws2_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Workspace 2", "slug": f"ws2-{uuid.uuid4().hex[:6]}"},
        headers=jwt_headers,
    )
    ws2_id = ws2_resp.json()["id"]

    # 2. Cria chave de API no Workspace 1
    key_resp = await client.post(
        f"/api/v1/workspaces/{ws1_id}/api-keys",
        json={"name": "Autonomous Agent Key", "scopes": ["*"]},
        headers=jwt_headers,
    )
    raw_key = key_resp.json()["raw_key"]

    # 3. Autenticação via header X-API-Key em /auth/me (sem cookie, sem JWT)
    me_resp_xkey = await client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": raw_key},
    )
    assert me_resp_xkey.status_code == 200
    assert me_resp_xkey.json()["email"] == email

    # 4. Autenticação via header Authorization: Bearer sf_live_...
    me_resp_bearer = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert me_resp_bearer.status_code == 200
    assert me_resp_bearer.json()["email"] == email

    # 5. Operação de domínio: Criar projeto no Workspace 1 usando a chave de API
    create_proj_resp = await client.post(
        f"/api/v1/workspaces/{ws1_id}/projects",
        json={"name": "Projeto Gerado por Agente IA", "description": "Criado via M2M PAT"},
        headers={"X-API-Key": raw_key},
    )
    assert create_proj_resp.status_code == 201
    assert create_proj_resp.json()["name"] == "Projeto Gerado por Agente IA"

    # 6. Tenant Isolation: Tentar acessar Workspace 2 com a chave de API do Workspace 1
    cross_tenant_resp = await client.post(
        f"/api/v1/workspaces/{ws2_id}/projects",
        json={"name": "Tentativa Invasora", "description": "Não deve permitir"},
        headers={"X-API-Key": raw_key},
    )
    assert cross_tenant_resp.status_code == 403
    assert "não possui autorização para operar neste workspace" in cross_tenant_resp.json()["message"]


@pytest.mark.asyncio
async def test_api_key_revoked_and_expired(client: AsyncClient) -> None:
    """Valida que chaves revogadas, expiradas ou adulteradas retornam 401 Unauthorized."""
    # 1. Usuário cria workspace e chave de API
    email = f"revoked_owner_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Revoked Owner"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    jwt_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Revocation Workspace", "slug": f"rev-ws-{uuid.uuid4().hex[:6]}"},
        headers=jwt_headers,
    )
    ws_id = ws_resp.json()["id"]

    key_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        json={"name": "Temp Key", "scopes": ["*"]},
        headers=jwt_headers,
    )
    key_data = key_resp.json()
    raw_key = key_data["raw_key"]
    key_id = key_data["id"]

    # 2. Chave inválida ou forjada retorna 401
    invalid_resp = await client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": "sf_live_chave_completamente_inexistente"},
    )
    assert invalid_resp.status_code == 401

    # 3. Revoga a chave e tenta utilizá-la
    await client.delete(
        f"/api/v1/workspaces/{ws_id}/api-keys/{key_id}",
        headers=jwt_headers,
    )

    revoked_resp = await client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": raw_key},
    )
    assert revoked_resp.status_code == 401
    assert "revogada ou expirada" in revoked_resp.json()["message"]

    # 4. Simulação de Chave expirada no banco
    async with TestingSessionLocal() as session:
        key_obj = await session.get(ApiKey, uuid.UUID(key_id))
        key_obj.is_revoked = False
        key_obj.expires_at = datetime.now(UTC) - timedelta(days=2)
        session.add(key_obj)
        await session.commit()

    expired_resp = await client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": raw_key},
    )
    assert expired_resp.status_code == 401
    assert "revogada ou expirada" in expired_resp.json()["message"]
