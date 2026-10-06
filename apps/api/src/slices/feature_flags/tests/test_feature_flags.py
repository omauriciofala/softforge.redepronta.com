import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_feature_flags_global_crud(client: AsyncClient) -> None:
    """Valida o ciclo de vida CRUD de feature flags globais e rejeição de chaves duplicadas."""
    # 1. Registro e autenticação
    email = f"ff_admin_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Flags Admin"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Cadastro de nova Feature Flag
    flag_key = f"beta_search_{uuid.uuid4().hex[:6]}"
    create_resp = await client.post(
        "/api/v1/system/features",
        json={
            "key": flag_key,
            "name": "Busca Inteligente Beta",
            "description": "Ativa novo algoritmo de busca semântica",
            "is_enabled": False,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    flag_data = create_resp.json()
    assert flag_data["key"] == flag_key
    assert flag_data["is_enabled"] is False
    flag_id = flag_data["id"]

    # 3. Listagem de flags globais
    list_resp = await client.get("/api/v1/system/features", headers=headers)
    assert list_resp.status_code == 200
    all_keys = [f["key"] for f in list_resp.json()]
    assert flag_key in all_keys

    # 4. Consulta por ID
    get_resp = await client.get(f"/api/v1/system/features/{flag_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == flag_id

    # 5. Atualização de estado global (ativação)
    update_resp = await client.patch(
        f"/api/v1/system/features/{flag_id}",
        json={"is_enabled": True, "name": "Busca Inteligente Beta (Ativada)"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_enabled"] is True
    assert update_resp.json()["name"] == "Busca Inteligente Beta (Ativada)"

    # 6. Rejeição de chave duplicada (HTTP 409)
    dup_resp = await client.post(
        "/api/v1/system/features",
        json={"key": flag_key, "name": "Duplicada", "is_enabled": True},
        headers=headers,
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"] == "FEATURE_FLAG_KEY_EXISTS"

    # 7. Exclusão da flag
    del_resp = await client.delete(f"/api/v1/system/features/{flag_id}", headers=headers)
    assert del_resp.status_code == 204

    # 8. Verificação de 404 após exclusão
    assert (
        await client.get(f"/api/v1/system/features/{flag_id}", headers=headers)
    ).status_code == 404


@pytest.mark.asyncio
async def test_workspace_feature_flags_evaluation_and_overrides(client: AsyncClient) -> None:
    """Valida a consolidação de flags e prioridade hierárquica (Workspace Override > Global Default)."""
    # 1. Usuário e Workspace
    email = f"ws_ff_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Workspace Flags User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Flags Workspace", "slug": f"flags-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Cadastro de duas flags globais: uma desligada e outra ligada
    suffix = uuid.uuid4().hex[:6]
    key_alpha = f"alpha_feature_{suffix}"
    key_beta = f"beta_feature_{suffix}"

    resp_a = await client.post(
        "/api/v1/system/features",
        json={"key": key_alpha, "name": "Feature Alpha", "is_enabled": False},
        headers=headers,
    )
    flag_a_id = resp_a.json()["id"]

    resp_b = await client.post(
        "/api/v1/system/features",
        json={"key": key_beta, "name": "Feature Beta", "is_enabled": True},
        headers=headers,
    )
    flag_b_id = resp_b.json()["id"]

    # 3. Avaliação inicial para o workspace (deve refletir o padrão global)
    eval_resp1 = await client.get(
        f"/api/v1/workspaces/{workspace_id}/features",
        headers=headers,
    )
    assert eval_resp1.status_code == 200
    flags_map1 = eval_resp1.json()["flags"]
    assert flags_map1[key_alpha] is False
    assert flags_map1[key_beta] is True

    # 4. Ativação via Override para Alpha no workspace (Global = False, Override = True)
    ov_resp_a = await client.post(
        f"/api/v1/workspaces/{workspace_id}/features/{flag_a_id}/override",
        json={"is_enabled": True},
        headers=headers,
    )
    assert ov_resp_a.status_code == 200
    assert ov_resp_a.json()["is_enabled"] is True

    # 5. Desativação via Override para Beta no workspace (Global = True, Override = False)
    ov_resp_b = await client.post(
        f"/api/v1/workspaces/{workspace_id}/features/{flag_b_id}/override",
        json={"is_enabled": False},
        headers=headers,
    )
    assert ov_resp_b.status_code == 200
    assert ov_resp_b.json()["is_enabled"] is False

    # 6. Nova avaliação consolidada (Overrides devem prevalecer)
    eval_resp2 = await client.get(
        f"/api/v1/workspaces/{workspace_id}/features",
        headers=headers,
    )
    flags_map2 = eval_resp2.json()["flags"]
    assert flags_map2[key_alpha] is True
    assert flags_map2[key_beta] is False

    # 7. Remoção do override de Beta (deve retornar ao padrão global True)
    rem_resp = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/features/{flag_b_id}/override",
        headers=headers,
    )
    assert rem_resp.status_code == 204

    eval_resp3 = await client.get(
        f"/api/v1/workspaces/{workspace_id}/features",
        headers=headers,
    )
    flags_map3 = eval_resp3.json()["flags"]
    assert flags_map3[key_beta] is True


@pytest.mark.asyncio
async def test_require_feature_flag_dependency_guard(client: AsyncClient) -> None:
    """Valida o bloqueio declarativo HTTP 403 de rotas protegidas por dependência require_feature_flag."""
    # 1. Usuário e Workspace
    email = f"guard_ff_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Guard User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Guard WS", "slug": f"guard-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Cadastro da flag 'beta_copilot' desabilitada globalmente
    # (Se já existir de outro teste, consulta ou cria)
    list_flags = await client.get("/api/v1/system/features", headers=headers)
    existing = next((f for f in list_flags.json() if f["key"] == "beta_copilot"), None)
    if existing:
        flag_id = existing["id"]
        # Garante que está False
        await client.patch(
            f"/api/v1/system/features/{flag_id}",
            json={"is_enabled": False},
            headers=headers,
        )
    else:
        resp = await client.post(
            "/api/v1/system/features",
            json={"key": "beta_copilot", "name": "Beta Copilot Guarded", "is_enabled": False},
            headers=headers,
        )
        flag_id = resp.json()["id"]

    # 3. Tentar acessar rota protegida -> Bloqueio HTTP 403 Forbidden
    guarded_url = f"/api/v1/workspaces/{workspace_id}/features/demo-guarded"
    blocked_resp = await client.get(guarded_url, headers=headers)
    assert blocked_resp.status_code == 403
    assert blocked_resp.json()["error"] == "FEATURE_FLAG_DISABLED"
    assert "beta_copilot" in blocked_resp.json()["message"]

    # 4. Ativar override específico para o workspace
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/features/{flag_id}/override",
        json={"is_enabled": True},
        headers=headers,
    )

    # 5. Acessar novamente a rota protegida -> Deve passar com HTTP 200
    allowed_resp = await client.get(guarded_url, headers=headers)
    assert allowed_resp.status_code == 200
    assert allowed_resp.json()["status"] == "allowed"
    assert allowed_resp.json()["feature"] == "beta_copilot"
