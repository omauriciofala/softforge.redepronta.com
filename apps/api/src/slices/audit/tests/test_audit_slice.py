import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import TestingSessionLocal
from src.core.queue.client import get_fake_queue
from src.core.queue.tasks import record_audit_log_task
from src.slices.audit.service import list_audit_logs


@pytest.mark.asyncio
async def test_audit_log_enqueued_on_login(client: AsyncClient) -> None:
    """Verifica se o login do usuário enfileira assincronamente o evento de auditoria."""
    fake_queue = get_fake_queue()
    fake_queue.clear()

    # 1. Cadastro
    email = f"audit_user_{uuid.uuid4().hex[:6]}@softforge.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Audit User"},
    )
    assert reg_resp.status_code == 201

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 3. Validação na fila
    audit_job = next(
        (j for j in fake_queue.jobs if j["function"] == "record_audit_log_task"),
        None,
    )
    assert audit_job is not None
    assert audit_job["kwargs"]["action"] == "auth.login"
    assert audit_job["kwargs"]["user_email"] == email
    assert audit_job["kwargs"]["resource_type"] == "user"


@pytest.mark.asyncio
async def test_record_audit_log_task_persists(db_session: AsyncSession) -> None:
    """Valida execução da task do Arq persistindo registro imutável no banco de dados."""
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ctx = {"session_maker": TestingSessionLocal}

    task_res = await record_audit_log_task(
        ctx=ctx,
        workspace_id=str(workspace_id),
        user_id=str(user_id),
        user_email="compliance@softforge.com",
        action="workspace.settings.updated",
        resource_type="workspace",
        resource_id=str(workspace_id),
        ip_address="192.168.1.100",
        user_agent="SoftForgeAgent/1.0",
    )
    assert task_res["status"] == "recorded"
    assert task_res["action"] == "workspace.settings.updated"

    # Consulta no banco
    items, total = await list_audit_logs(db_session, workspace_id)
    assert total == 1
    assert items[0].action == "workspace.settings.updated"
    assert items[0].user_email == "compliance@softforge.com"
    assert items[0].ip_address == "192.168.1.100"


@pytest.mark.asyncio
async def test_audit_logs_rbac_and_api(client: AsyncClient) -> None:
    """Verifica proteção RBAC (mínimo Admin/Owner) para consulta de logs de auditoria."""
    # 1. Usuário 1 cria workspace (torna-se Owner)
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "Password123!", "full_name": "Owner User"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    owner_token = login_res.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Compliance Workspace", "slug": f"compliance-{uuid.uuid4().hex[:6]}"},
        headers=owner_headers,
    )
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 2. Persiste 2 logs diretamente para o workspace
    ctx = {"session_maker": TestingSessionLocal}
    await record_audit_log_task(
        ctx=ctx,
        workspace_id=str(workspace_id),
        action="project.created",
        resource_type="project",
    )
    await record_audit_log_task(
        ctx=ctx,
        workspace_id=str(workspace_id),
        action="member.invited",
        resource_type="workspace_member",
    )

    # 3. Owner consulta logs (200 OK)
    get_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/audit-logs",
        headers=owner_headers,
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 4. Outro usuário sem acesso tenta consultar (403 Forbidden)
    stranger_email = f"stranger_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": stranger_email, "password": "Password123!", "full_name": "Stranger"},
    )
    stranger_login = await client.post(
        "/api/v1/auth/login",
        json={"email": stranger_email, "password": "Password123!"},
    )
    stranger_headers = {"Authorization": f"Bearer {stranger_login.json()['access_token']}"}

    forbidden_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/audit-logs",
        headers=stranger_headers,
    )
    assert forbidden_res.status_code == 403
