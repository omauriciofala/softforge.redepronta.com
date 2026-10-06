import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_projects_and_tasks_crud_flow(client: AsyncClient) -> None:
    # 1. Usuário cria conta e obtém token
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pm@softforge.com",
            "password": "Password123!",
            "full_name": "Product Manager",
        },
    )
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "pm@softforge.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. Cria workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Engineering Workspace"},
        headers=headers,
    )
    workspace_id = ws_res.json()["id"]

    # 3. Cria projeto dentro do workspace
    proj_payload = {
        "name": "SoftForge Framework Release",
        "description": "Desenvolvimento do framework fullstack AI-native",
    }
    proj_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json=proj_payload,
        headers=headers,
    )
    assert proj_res.status_code == 201, proj_res.text
    proj_data = proj_res.json()
    assert proj_data["name"] == proj_payload["name"]
    project_id = proj_data["id"]

    # 4. Adiciona tarefa ao projeto
    task_payload = {
        "title": "Configurar Orval e sincronização OpenAPI",
        "status": "in_progress",
        "priority": "high",
    }
    task_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/tasks",
        json=task_payload,
        headers=headers,
    )
    assert task_res.status_code == 201, task_res.text
    task_data = task_res.json()
    assert task_data["title"] == task_payload["title"]
    assert task_data["status"] == "in_progress"

    # 5. Lista projetos do workspace e valida tasks_count
    list_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["tasks_count"] == 1

    # 6. Atualização parcial do projeto
    patch_res = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        json={"name": "SoftForge Core Engine v1.0"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "SoftForge Core Engine v1.0"
