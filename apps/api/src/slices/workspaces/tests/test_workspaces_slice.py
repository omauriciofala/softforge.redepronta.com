import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_and_rbac_flow(client: AsyncClient) -> None:
    """Valida ciclo completo de criação de workspace, RBAC, alteração de cargos e exclusão de membro."""
    # 1. Cria usuário Owner
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@company.com"
    owner_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": owner_email,
            "password": "Password123!",
            "full_name": "Workspace Owner",
        },
    )
    assert owner_reg.status_code == 201
    owner_token_res = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    owner_headers = {"Authorization": f"Bearer {owner_token_res.json()['access_token']}"}

    # 2. Cria usuário Convidado
    guest_email = f"guest_{uuid.uuid4().hex[:6]}@company.com"
    guest_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": guest_email,
            "password": "Password123!",
            "full_name": "Guest Member",
        },
    )
    assert guest_reg.status_code == 201
    guest_data = guest_reg.json()
    guest_user_id = guest_data["id"]

    guest_token_res = await client.post(
        "/api/v1/auth/login",
        json={"email": guest_email, "password": "Password123!"},
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
        json={"email": guest_email, "role": "member"},
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

    # 7. Owner promove Guest para ADMIN
    patch_role_res = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{guest_user_id}",
        json={"role": "admin"},
        headers=owner_headers,
    )
    assert patch_role_res.status_code == 200
    assert patch_role_res.json()["role"] == "admin"

    # 8. Proteção do Owner: tentativa de remover o Owner deve retornar 400
    owner_user_id = ws_data["owner_id"]
    cannot_remove_owner = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_user_id}",
        headers=owner_headers,
    )
    assert cannot_remove_owner.status_code == 400

    # 9. Remoção do Guest do workspace
    remove_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{guest_user_id}",
        headers=owner_headers,
    )
    assert remove_res.status_code == 204

    # 10. Guest tenta acessar novamente e recebe 403
    forbidden_again = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=guest_headers,
    )
    assert forbidden_again.status_code == 403


@pytest.mark.asyncio
async def test_workspace_invites_flow_and_acceptance(client: AsyncClient) -> None:
    """Valida fluxo de envio de convite, renovação, aceitação e revogação."""
    # 1. Cria usuário Admin/Owner
    admin_email = f"ws_admin_{uuid.uuid4().hex[:6]}@enterprise.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "Password123!", "full_name": "Team Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "Password123!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 2. Cria Workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Enterprise Workspace"},
        headers=admin_headers,
    )
    workspace_id = ws_res.json()["id"]

    # 3. Envia convite de equipe para novo colaborador
    invite_email = f"developer_{uuid.uuid4().hex[:6]}@external.com"
    invite_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": invite_email, "role": "member"},
        headers=admin_headers,
    )
    assert invite_res.status_code == 201
    invite_data = invite_res.json()
    assert invite_data["email"] == invite_email
    assert invite_data["role"] == "member"
    assert invite_data["status"] == "pending"
    assert "token" in invite_data
    token = invite_data["token"]
    assert invite_data["id"] is not None

    # 4. Listar convites ativos
    list_invites_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/invites",
        headers=admin_headers,
    )
    assert list_invites_res.status_code == 200
    assert list_invites_res.json()["total"] >= 1

    # 5. Criar conta do desenvolvedor convidado
    await client.post(
        "/api/v1/auth/register",
        json={"email": invite_email, "password": "Password123!", "full_name": "Dev Collaborator"},
    )
    dev_login = await client.post(
        "/api/v1/auth/login",
        json={"email": invite_email, "password": "Password123!"},
    )
    dev_headers = {"Authorization": f"Bearer {dev_login.json()['access_token']}"}

    # 6. Desenvolvedor aceita o convite via token
    accept_res = await client.post(
        "/api/v1/workspaces/invites/accept",
        json={"token": token},
        headers=dev_headers,
    )
    assert accept_res.status_code == 200
    accepted_ws = accept_res.json()
    assert accepted_ws["id"] == workspace_id
    assert accepted_ws["role"] == "member"

    # 7. Desenvolvedor agora consegue visualizar o workspace
    ws_view = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=dev_headers,
    )
    assert ws_view.status_code == 200

    # 8. Não é permitido convidar alguém que já é membro ativo
    duplicate_invite_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": invite_email, "role": "viewer"},
        headers=admin_headers,
    )
    assert duplicate_invite_res.status_code == 400
    assert "já é membro ativo" in duplicate_invite_res.json()["message"]

    # 9. Teste de revogação de convite
    other_email = f"other_{uuid.uuid4().hex[:6]}@external.com"
    other_invite_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": other_email, "role": "viewer"},
        headers=admin_headers,
    )
    other_invite_id = other_invite_res.json()["id"]
    other_token = other_invite_res.json()["token"]

    revoke_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/invites/{other_invite_id}",
        headers=admin_headers,
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"

    # Tentativa de aceitar convite revogado deve falhar
    failed_accept = await client.post(
        "/api/v1/workspaces/invites/accept",
        json={"token": other_token},
        headers=dev_headers,
    )
    assert failed_accept.status_code == 404
