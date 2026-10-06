import pytest
from httpx import AsyncClient

from src.core.queue.client import FakeQueueClient, get_fake_queue
from src.core.queue.tasks import (
    cleanup_revoked_tokens,
    process_subscription_renewal,
    send_transactional_email,
)


@pytest.mark.asyncio
async def test_fake_queue_operations() -> None:
    """Verifica operações em memória do FakeQueueClient."""
    fake_queue = FakeQueueClient()
    assert fake_queue.enqueued_count == 0

    job_id = await fake_queue.enqueue(
        "send_transactional_email",
        to_email="dev@softforge.com",
        subject="Boas-vindas!",
        body_html="<p>Olá</p>",
    )
    assert job_id.startswith("fake-job-")
    assert fake_queue.enqueued_count == 1
    assert fake_queue.jobs[0]["function"] == "send_transactional_email"
    assert fake_queue.jobs[0]["kwargs"]["to_email"] == "dev@softforge.com"

    fake_queue.clear()
    assert fake_queue.enqueued_count == 0


@pytest.mark.asyncio
async def test_register_dispatches_background_welcome_email(client: AsyncClient) -> None:
    """Valida se o cadastro de usuário enfileira assincronamente a tarefa de e-mail de boas-vindas."""
    fake_queue = get_fake_queue()
    fake_queue.clear()

    reg_payload = {
        "email": "worker_user@softforge.com",
        "password": "StrongPassword123!",
        "full_name": "Usuário Worker",
    }
    response = await client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201

    # Verifica se a FakeQueue capturou o disparo
    assert fake_queue.enqueued_count >= 1
    email_job = next(j for j in fake_queue.jobs if j["function"] == "send_transactional_email")
    assert email_job["kwargs"]["to_email"] == "worker_user@softforge.com"
    assert "Bem-vindo" in email_job["kwargs"]["subject"]


@pytest.mark.asyncio
async def test_tasks_direct_execution() -> None:
    """Verifica execução direta das tarefas assíncronas do Arq Worker."""
    from conftest import TestingSessionLocal

    ctx: dict = {"session_maker": TestingSessionLocal}

    # 1. Tarefa de envio de e-mail
    email_res = await send_transactional_email(
        ctx,
        to_email="teste@dominio.com",
        subject="Assunto de Teste",
        body_html="<p>Conteúdo</p>",
    )
    assert email_res["status"] == "sent"
    assert email_res["to_email"] == "teste@dominio.com"

    # 2. Tarefa de reconciliação de assinatura
    renewal_res = await process_subscription_renewal(ctx, subscription_id="sub_test_001")
    assert renewal_res["status"] == "processed"
    assert renewal_res["subscription_id"] == "sub_test_001"

    # 3. Tarefa de limpeza de tokens
    cleanup_res = await cleanup_revoked_tokens(ctx)
    assert "deleted_count" in cleanup_res
    assert isinstance(cleanup_res["deleted_count"], int)
