import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient) -> None:
    # 1. Registro
    reg_payload = {
        "email": "developer@softforge.com",
        "password": "SuperSecretPassword123!",
        "full_name": "Agente AI Developer",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()
    assert user_data["email"] == "developer@softforge.com"
    assert user_data["full_name"] == "Agente AI Developer"
    assert "id" in user_data

    # 2. Login com sucesso
    login_payload = {
        "email": "developer@softforge.com",
        "password": "SuperSecretPassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200, login_res.text
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Consulta ao /me com o Bearer token
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_data["id"]
    assert me_data["email"] == "developer@softforge.com"

    # 4. Login com senha errada
    bad_login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "developer@softforge.com", "password": "WrongPassword!"},
    )
    assert bad_login_res.status_code == 401
