import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import TestingSessionLocal
from src.core.queue.client import get_fake_queue
from src.core.queue.tasks import dispatch_webhook_task
from src.slices.webhooks.security import (
    generate_webhook_signature,
    verify_webhook_signature,
)


def test_hmac_signature_generation_and_verification() -> None:
    """Valida geração e verificação criptográfica da assinatura HMAC-SHA256 do webhook."""
    secret = "whsec_test_secret_1234567890abcdef"
    payload = {"event": "project.created", "project_id": "proj_123", "name": "SoftForge"}

    sig_header = generate_webhook_signature(secret, payload)
    assert "t=" in sig_header
    assert "v1=" in sig_header

    # 1. Verificação bem-sucedida
    assert verify_webhook_signature(secret, payload, sig_header) is True

    # 2. Carga adulterada deve falhar
    tampered_payload = {"event": "project.created", "project_id": "proj_123", "name": "Adulterado"}
    assert verify_webhook_signature(secret, tampered_payload, sig_header) is False

    # 3. Segredo incorreto deve falhar
    assert verify_webhook_signature("whsec_wrong_secret", payload, sig_header) is False

    # 4. Timestamp expirado além da tolerância
    old_sig = generate_webhook_signature(secret, payload, timestamp=1000)
    assert verify_webhook_signature(secret, payload, old_sig, tolerance_seconds=300) is False


@pytest.mark.asyncio
async def test_webhook_endpoints_crud_and_rbac(client: AsyncClient) -> None:
    """Valida cadastro, consulta, atualização e proteção RBAC de webhooks do workspace."""
    # 1. Usuário cria workspace
    owner_email = f"wh_owner_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "Password123!", "full_name": "WH Owner"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Webhook Workspace", "slug": f"wh-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Cadastra webhook
    create_payload = {
        "url": "mock://customer.api/webhooks",
        "description": "Integração Slack",
        "events": ["project.created"],
    }
    ep_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/webhooks",
        json=create_payload,
        headers=headers,
    )
    assert ep_resp.status_code == 201
    ep_data = ep_resp.json()
    assert ep_data["url"] == "mock://customer.api/webhooks"
    assert ep_data["secret"].startswith("whsec_")
    assert ep_data["is_active"] is True
    endpoint_id = ep_data["id"]

    # 3. Listagem
    list_resp = await client.get(f"/api/v1/workspaces/{workspace_id}/webhooks", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 4. Atualização
    patch_resp = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/webhooks/{endpoint_id}",
        json={"description": "Integração Atualizada", "events": ["*"]},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["description"] == "Integração Atualizada"
    assert patch_resp.json()["events"] == ["*"]

    # 5. Outro usuário sem permissão tenta acessar
    stranger_email = f"wh_stranger_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": stranger_email, "password": "Password123!", "full_name": "Stranger"},
    )
    s_login = await client.post(
        "/api/v1/auth/login",
        json={"email": stranger_email, "password": "Password123!"},
    )
    s_headers = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

    forbidden_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/webhooks",
        headers=s_headers,
    )
    assert forbidden_resp.status_code == 403


@pytest.mark.asyncio
async def test_project_created_triggers_webhook_delivery(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verifica se a criação de um projeto dispara o evento para endpoints inscritos e processa a entrega via worker."""
    fake_queue = get_fake_queue()
    fake_queue.clear()

    # 1. Usuário cria workspace
    owner_email = f"proj_wh_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "Password123!", "full_name": "Project WH"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Auto Trigger WS", "slug": f"autotrigger-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    workspace_id = ws_resp.json()["id"]

    # 2. Registra endpoint mock
    ep_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/webhooks",
        json={"url": "mock://receiver.internal/hooks", "events": ["project.created"]},
        headers=headers,
    )
    endpoint_id = ep_resp.json()["id"]

    # 3. Cria projeto no workspace
    proj_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Projeto Webhook Ativado", "description": "Gera webhook"},
        headers=headers,
    )
    assert proj_resp.status_code == 201

    # 4. Valida se a tarefa dispatch_webhook_task foi enfileirada no FakeQueue
    wh_jobs = [j for j in fake_queue.jobs if j["function"] == "dispatch_webhook_task"]
    assert len(wh_jobs) == 1
    delivery_id = wh_jobs[0]["kwargs"]["delivery_id"]

    # 5. Executa a tarefa do worker com o contexto do banco de teste
    ctx = {"session_maker": TestingSessionLocal}
    task_res = await dispatch_webhook_task(ctx, delivery_id=delivery_id)
    assert task_res["status"] == "success"

    # 6. Valida consulta do histórico de entregas via API
    deliv_resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/webhooks/{endpoint_id}/deliveries",
        headers=headers,
    )
    assert deliv_resp.status_code == 200
    deliveries = deliv_resp.json()
    assert deliveries["total"] == 1
    assert deliveries["items"][0]["status"] == "success"
    assert deliveries["items"][0]["response_status_code"] == 200
