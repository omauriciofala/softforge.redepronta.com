import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from src.main import app
from src.slices.auth.service import get_user_by_email
from src.slices.notifications.service import create_and_send_notification


@pytest.mark.asyncio
async def test_notifications_crud_and_counts(client: AsyncClient, db_session: AsyncSession) -> None:
    """Valida ciclo completo de notificações in-app: criação, contagem de não lidas e marcação de leitura."""
    # 1. Cadastro e login
    email = f"notify_user_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Notify User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = await get_user_by_email(db_session, email)
    assert user is not None

    # 2. Cria notificação diretamente no banco/serviço
    n1 = await create_and_send_notification(
        session=db_session,
        user_id=user.id,
        title="Novo Projeto Criado",
        message="O projeto 'Alpha' foi inicializado com sucesso.",
        category="project",
    )

    # 3. Consulta badge de não lidas
    badge_resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert badge_resp.status_code == 200
    assert badge_resp.json()["unread_count"] == 1

    # 4. Lista notificações
    list_resp = await client.get("/api/v1/notifications", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert data["items"][0]["title"] == "Novo Projeto Criado"
    assert data["items"][0]["is_read"] is False

    # 5. Marca como lida
    read_resp = await client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # 6. Contador deve zerar
    badge_after = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert badge_after.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_notifications_read(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verifica atualização em lote de todas as notificações pendentes."""
    email = f"batch_user_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Batch User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    user = await get_user_by_email(db_session, email)
    assert user is not None

    for i in range(3):
        await create_and_send_notification(
            session=db_session,
            user_id=user.id,
            title=f"Notificação {i}",
            message=f"Conteúdo {i}",
        )

    # Marca todas como lidas
    mark_all = await client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark_all.status_code == 200
    assert mark_all.json()["marked_count"] == 3

    # Badge zerado
    badge = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert badge.json()["unread_count"] == 0


def test_websocket_realtime_ping_pong() -> None:
    """Verifica conexão WebSocket autenticada e protocolo ping/pong."""
    from src.core.security import create_access_token

    test_user_id = uuid.uuid4()
    token = create_access_token({"sub": str(test_user_id)})

    with TestClient(app).websocket_connect(f"/api/v1/notifications/ws?token={token}") as ws:
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
        assert data == {"type": "pong"}
