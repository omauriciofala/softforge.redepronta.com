import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_system_themes_discovery(client: AsyncClient) -> None:
    """Valida a detecção dinâmica de temas instalados no diretório themes/ e o contrato do manifesto."""
    # 1. Listar todos os temas do sistema
    list_resp = await client.get("/api/v1/system/themes")
    assert list_resp.status_code == 200
    themes = list_resp.json()
    assert isinstance(themes, list)
    assert len(themes) >= 2

    slugs = [t["slug"] for t in themes]
    assert "default-react" in slugs
    assert "bootstrap-starter" in slugs

    bootstrap_theme = next(t for t in themes if t["slug"] == "bootstrap-starter")
    assert bootstrap_theme["engine"] == "html-bootstrap"
    assert "tokens" in bootstrap_theme
    assert "colors" in bootstrap_theme["tokens"]

    # 2. Obter manifesto detalhado de tema existente
    get_resp = await client.get("/api/v1/system/themes/bootstrap-starter")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["name"] == "SoftForge Bootstrap Starter"
    assert detail["engine"] == "html-bootstrap"
    assert detail["tokens"]["colors"]["primary"] == "#4f46e5"

    # 3. Consultar tema inexistente deve retornar HTTP 404
    not_found_resp = await client.get("/api/v1/system/themes/inexistente-slug-xyz")
    assert not_found_resp.status_code == 404
    assert not_found_resp.json()["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_workspace_theme_lifecycle_and_branding(client: AsyncClient) -> None:
    """Valida consulta de tema padrão, customização white-labeling e injeção de tokens CSS (--sf-*)."""
    # 1. Registro e login do usuário
    email = f"theme_owner_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Theme Owner"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Criação do workspace
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Branding Workspace", "slug": f"brand-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    # 3. Consulta de tema inicial (deve retornar os padrões do default-react)
    initial_theme_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/theme",
        headers=headers,
    )
    assert initial_theme_resp.status_code == 200
    initial_data = initial_theme_resp.json()
    assert initial_data["theme_slug"] == "default-react"
    assert initial_data["theme_engine"] == "react"
    assert initial_data["custom_logo_url"] is None
    assert "--sf-color-primary" in initial_data["css_variables"]
    assert "--sf-radius" in initial_data["css_variables"]

    # 4. Atualização de White-Labeling (altera slug para bootstrap-starter, cor primária e logo)
    custom_color = "#ff5500"
    custom_logo = "https://cdn.example.com/logo-client.png"
    update_resp = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/theme",
        json={
            "theme_slug": "bootstrap-starter",
            "custom_primary_color": custom_color,
            "custom_logo_url": custom_logo,
            "custom_css": "body { letter-spacing: 0.5px; }",
            "tokens_override": {
                "geometry": {"border_radius": "1rem"},
            },
        },
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["theme_slug"] == "bootstrap-starter"
    assert updated_data["theme_engine"] == "html-bootstrap"
    assert updated_data["custom_primary_color"] == custom_color
    assert updated_data["custom_logo_url"] == custom_logo
    assert updated_data["custom_css"] == "body { letter-spacing: 0.5px; }"
    # Confirma precedência da cor primária customizada nas variáveis CSS
    assert updated_data["css_variables"]["--sf-color-primary"] == custom_color
    # Confirma override do raio de borda
    assert updated_data["css_variables"]["--sf-radius"] == "1rem"

    # 5. Tentativa de atribuir slug inexistente deve retornar HTTP 400 THEME_NOT_FOUND
    invalid_slug_resp = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/theme",
        json={"theme_slug": "tema-fantasioso-inexistente"},
        headers=headers,
    )
    assert invalid_slug_resp.status_code == 400
    assert invalid_slug_resp.json()["error"] == "THEME_NOT_FOUND"


@pytest.mark.asyncio
async def test_workspace_theme_rbac_permissions(client: AsyncClient) -> None:
    """Valida RBAC: visualizadores (VIEWER) podem consultar tokens, mas apenas ADMIN/OWNER pode atualizar."""
    # 1. Proprietário cria workspace
    owner_email = f"owner_rbac_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "Password123!", "full_name": "Workspace Owner"},
    )
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "RBAC Workspace", "slug": f"rbac-ws-{uuid.uuid4().hex[:6]}"},
        headers=owner_headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Registro de um segundo usuário que será convidado como VIEWER
    viewer_email = f"viewer_rbac_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": viewer_email, "password": "Password123!", "full_name": "Viewer User"},
    )
    viewer_login = await client.post(
        "/api/v1/auth/login",
        json={"email": viewer_email, "password": "Password123!"},
    )
    viewer_headers = {"Authorization": f"Bearer {viewer_login.json()['access_token']}"}

    # 3. Adicionar membro com papel 'viewer'
    member_add_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": viewer_email, "role": "viewer"},
        headers=owner_headers,
    )
    assert member_add_resp.status_code == 201

    # 4. Viewer pode ler tema do workspace (HTTP 200)
    viewer_get_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/theme",
        headers=viewer_headers,
    )
    assert viewer_get_resp.status_code == 200

    # 5. Viewer tenta modificar tema -> Bloqueio HTTP 403 Forbidden
    viewer_patch_resp = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/theme",
        json={"custom_primary_color": "#112233"},
        headers=viewer_headers,
    )
    assert viewer_patch_resp.status_code == 403
    assert viewer_patch_resp.json()["error"] == "FORBIDDEN"
