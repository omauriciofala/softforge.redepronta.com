import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plans(client: AsyncClient) -> None:
    """Verifica que o catálogo de planos retorna Free, Pro e Enterprise."""
    resp = await client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    tiers = [p["tier"] for p in data]
    assert "free" in tiers
    assert "pro" in tiers
    assert "enterprise" in tiers


@pytest.mark.asyncio
async def test_subscription_lifecycle_and_checkout_pix(client: AsyncClient) -> None:
    """Testa o ciclo completo: usuário novo inicia no Free e realiza checkout Pix do Pro."""
    # 1. Registra e autentica usuário
    user_email = f"billing_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": "SecurePassword123!", "full_name": "Billing User"},
    )
    assert reg_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Consulta assinatura padrão (deve ser Free)
    sub_resp = await client.get("/api/v1/billing/subscription", headers=headers)
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["plan_tier"] == "free"
    assert sub_data["status"] == "active"
    assert sub_data["max_projects"] == 3

    # 3. Dispara Checkout Pix para o Plano Pro
    checkout_payload = {
        "target_type": "personal",
        "plan_tier": "pro",
        "payment_method": "pix",
        "payer_email": user_email,
        "payer_cpf_cnpj": "12345678900",
    }
    checkout_resp = await client.post("/api/v1/billing/checkout", json=checkout_payload, headers=headers)
    assert checkout_resp.status_code == 201
    checkout_data = checkout_resp.json()

    assert "invoice" in checkout_data
    invoice = checkout_data["invoice"]
    assert invoice["amount_cents"] == 4900
    assert invoice["payment_method"] == "pix"
    assert invoice["pix_copy_paste"] is not None
    assert invoice["pix_qr_code"] is not None
    assert "provider_payment_id" in checkout_data["subscription"] or invoice["status"] == "pending"

    # 4. Simula Webhook do Mercado Pago aprovando a cobrança
    payment_id = invoice.get("provider_payment_id") or "mp_mock_payment_123"
    webhook_payload = {
        "action": "payment.created",
        "type": "payment",
        "data": {"id": payment_id},
    }
    wh_resp = await client.post("/api/v1/billing/webhooks/mercadopago", json=webhook_payload)
    assert wh_resp.status_code == 200
    assert wh_resp.json()["received"] is True

    # 5. Consulta assinatura novamente após webhook: agora é Pro!
    upgraded_resp = await client.get("/api/v1/billing/subscription", headers=headers)
    assert upgraded_resp.status_code == 200
    upgraded_sub = upgraded_resp.json()
    assert upgraded_sub["plan_tier"] == "pro"
    assert upgraded_sub["max_projects"] == 25


@pytest.mark.asyncio
async def test_quota_blocks_excess_projects(client: AsyncClient) -> None:
    """Valida que a dependência check_quota bloqueia criação de projetos que excedem o plano Free (3 projetos)."""
    # 1. Registra usuário e faz login
    user_email = f"quota_user_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": "SecurePassword123!", "full_name": "Quota User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "SecurePassword123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Cria workspace
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Quota Test Workspace", "slug": f"quota-ws-{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    assert ws_resp.status_code == 201
    ws_id = ws_resp.json()["id"]

    # 3. Cria 3 projetos (limite máximo do plano Free)
    for i in range(1, 4):
        p_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/projects",
            json={"name": f"Projeto #{i}", "description": "Teste"},
            headers=headers,
        )
        assert p_resp.status_code == 201

    # 4. Tenta criar o 4º projeto: deve ser bloqueado com 403 Forbidden!
    blocked_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Projeto #4 (Excedente)", "description": "Deve falhar"},
        headers=headers,
    )
    assert blocked_resp.status_code == 403
    assert "Limite de projetos atingido" in blocked_resp.json()["message"]

    # 5. Faz upgrade para o plano Pro via checkout Pix e webhook
    checkout_resp = await client.post(
        "/api/v1/billing/checkout",
        json={
            "target_type": "workspace",
            "workspace_id": ws_id,
            "plan_tier": "pro",
            "payment_method": "pix",
            "payer_email": user_email,
        },
        headers=headers,
    )
    assert checkout_resp.status_code == 201
    payment_id = checkout_resp.json()["invoice"]["provider_payment_id"]

    # Simula webhook de aprovação do pagamento
    await client.post(
        "/api/v1/billing/webhooks/mercadopago",
        json={"action": "payment.created", "data": {"id": payment_id}},
    )

    # 6. Tenta novamente criar o 4º projeto: agora tem quota e deve passar com 201 Created!
    allowed_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Projeto #4 (Agora Permitido no Pro)", "description": "Deve passar"},
        headers=headers,
    )
    assert allowed_resp.status_code == 201

