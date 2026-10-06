import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_storage_upload_download_and_delete_flow(client: AsyncClient) -> None:
    """Valida ciclo completo de upload, download, listagem e exclusão de arquivos no workspace."""
    # 1. Usuário cria conta e workspace
    email = f"storage_user_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Storage User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Storage Workspace", "slug": f"storage-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Upload de arquivo binário / texto
    file_bytes = b"SoftForge AI Framework - Storage Vertical Slice Content"
    upload_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/storage/upload",
        files={"file": ("relatorio_arquitetura.txt", file_bytes, "text/plain")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    file_data = upload_resp.json()
    assert file_data["filename"] == "relatorio_arquitetura.txt"
    assert file_data["file_size_bytes"] == len(file_bytes)
    assert "download_url" in file_data
    file_id = file_data["id"]

    # 3. Listagem de arquivos do workspace
    list_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/storage/files",
        headers=headers,
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(f["id"] == file_id for f in list_data["items"])

    # 4. Download autenticado do arquivo
    download_resp = await client.get(
        f"/api/v1/storage/files/{file_id}/download",
        headers=headers,
    )
    assert download_resp.status_code == 200
    assert download_resp.content == file_bytes
    assert "text/plain" in download_resp.headers["content-type"]

    # 5. Exclusão do arquivo
    del_resp = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/storage/files/{file_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204

    # 6. Nova tentativa de download deve retornar 404
    after_del_resp = await client.get(
        f"/api/v1/storage/files/{file_id}/download",
        headers=headers,
    )
    assert after_del_resp.status_code == 404


@pytest.mark.asyncio
async def test_storage_tenant_isolation(client: AsyncClient) -> None:
    """Garante que usuários de outros workspaces não conseguem baixar arquivos privados."""
    # 1. Cria Workspace 1 com Usuário 1
    u1_email = f"user1_{uuid.uuid4().hex[:6]}@tenant1.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": u1_email, "password": "Password123!", "full_name": "Tenant 1 User"},
    )
    u1_login = await client.post(
        "/api/v1/auth/login",
        json={"email": u1_email, "password": "Password123!"},
    )
    u1_headers = {"Authorization": f"Bearer {u1_login.json()['access_token']}"}

    ws1_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Tenant 1 Workspace", "slug": f"t1-{uuid.uuid4().hex[:6]}"},
        headers=u1_headers,
    )
    ws1_id = ws1_resp.json()["id"]

    # 2. Upload de arquivo confidencial no Workspace 1
    secret_bytes = b"TOP SECRET FINANCIAL REPORT"
    up_resp = await client.post(
        f"/api/v1/workspaces/{ws1_id}/storage/upload",
        files={"file": ("confidencial.txt", secret_bytes, "text/plain")},
        headers=u1_headers,
    )
    file_id = up_resp.json()["id"]

    # 3. Cria Workspace 2 com Usuário 2
    u2_email = f"user2_{uuid.uuid4().hex[:6]}@tenant2.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": u2_email, "password": "Password123!", "full_name": "Tenant 2 User"},
    )
    u2_login = await client.post(
        "/api/v1/auth/login",
        json={"email": u2_email, "password": "Password123!"},
    )
    u2_headers = {"Authorization": f"Bearer {u2_login.json()['access_token']}"}

    # 4. Usuário 2 tenta baixar arquivo do Workspace 1 (deve receber 403 Forbidden)
    forbidden_resp = await client.get(
        f"/api/v1/storage/files/{file_id}/download",
        headers=u2_headers,
    )
    assert forbidden_resp.status_code == 403
    assert "não possui autorização" in forbidden_resp.json()["message"]


@pytest.mark.asyncio
async def test_avatar_upload_updates_user_profile(client: AsyncClient) -> None:
    """Valida upload de avatar de usuário, atualização do perfil e acesso público ao arquivo."""
    # 1. Cria usuário
    email = f"avatar_user_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Avatar User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Upload de avatar
    avatar_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    avatar_resp = await client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("profile.png", avatar_bytes, "image/png")},
        headers=headers,
    )
    assert avatar_resp.status_code == 200
    avatar_data = avatar_resp.json()
    assert "avatar_url" in avatar_data
    avatar_url = avatar_data["avatar_url"]

    # 3. Consulta perfil do usuário (/auth/me) e valida avatar_url atualizado
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["avatar_url"] == avatar_url

    # 4. Acesso público ao avatar (sem cabeçalho de autenticação)
    public_avatar_resp = await client.get(avatar_url)
    assert public_avatar_resp.status_code == 200
    assert public_avatar_resp.content == avatar_bytes
