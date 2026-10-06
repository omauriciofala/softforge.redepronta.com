import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_and_rbac_flow(client: AsyncClient) -> None:
    # 1. Cria usuário Owner
    owner_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@company.com",
            "password": "Password123!",
            "full_name": "Workspace Owner",
        },
    )
    assert owner_reg.status_code == 201
    owner_token_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@company.com", "password": "Password123!"},
    )
    owner_headers = {"Authorization": f"Bearer {owner_token_res.json()['access_token']}"}

    # 2. Cria usuário Convidado
    guest_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "guest@company.com",
            "password": "Password123!",
            "full_name": "Guest Member",
        },
    )
    assert guest_reg.status_code == 201
    guest_token_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "guest@company.com", "password": "Password123!"},
    )
    guest_headers = {"Authorization": f"Bearer {guest_token_res.json()['access_token']}"}

    # 3. Owner cria um workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Acme Corporation"},
        headers=owner_headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    ws_data = ws_res.json()
    assert ws_data["name"] == "Acme Corporation"
    assert ws_data["role"] == "owner"
    workspace_id = ws_data["id"]

    # 4. Guest tenta acessar o workspace antes de ser adicionado (deve receber 403 Forbidden)
    forbidden_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=guest_headers,
    )
    assert forbidden_res.status_code == 403

    # 5. Owner adiciona Guest como MEMBER
    add_member_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": "guest@company.com", "role": "member"},
        headers=owner_headers,
    )
    assert add_member_res.status_code == 201, add_member_res.text
    assert add_member_res.json()["role"] == "member"

    # 6. Guest agora consegue acessar e visualizar membros
    guest_view_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=guest_headers,
    )
    assert guest_view_res.status_code == 200
    members = guest_view_res.json()
    assert len(members) == 2
