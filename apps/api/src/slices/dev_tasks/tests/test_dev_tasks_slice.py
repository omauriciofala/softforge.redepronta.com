import json
import sys

import pytest
from httpx import AsyncClient

from src.slices.dev_tasks.mcp import handle_tool_call


@pytest.mark.asyncio
async def test_dev_tasks_api_lifecycle(client: AsyncClient) -> None:
    # 1. Usuário cria conta e obtém token
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "agent_tester@softforge.com",
            "password": "Password123!",
            "full_name": "Agent Tester",
        },
    )
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "agent_tester@softforge.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. Cria workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "DevTasks AI Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 3. Cria tarefa de desenvolvimento
    create_payload = {
        "title": "Criar slice de testes e MCP",
        "description": "Implementar endpoints REST e protocolo stdio MCP",
        "task_type": "feature",
        "priority": "high",
        "target_files": ["apps/api/src/slices/dev_tasks/router.py"],
        "acceptance_criteria": ["Rotas respondem 200/201", "Verificação estrita aprovada"],
        "verification_command": "echo Success",
        "git_branch": "feature/dev-tasks",
    }
    task_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks",
        json=create_payload,
        headers=headers,
    )
    assert task_res.status_code == 201, task_res.text
    task_data = task_res.json()
    assert task_data["title"] == create_payload["title"]
    assert task_data["status"] == "todo"
    task_id = task_data["id"]

    # 4. Listar tarefas com filtros
    list_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks?status=todo&priority=high",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 5. Obter detalhes da tarefa
    get_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 6. Atualizar tarefa
    patch_res = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}",
        json={"priority": "urgent"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["priority"] == "urgent"

    # 7. Agente assume a tarefa (claim)
    claim_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}/claim",
        json={"agent_name": "antigravity"},
        headers=headers,
    )
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "in_progress"
    assert claim_res.json()["assigned_agent"] == "antigravity"

    # 8. Adicionar anotação de progresso (notes)
    note_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}/notes",
        json={
            "author": "antigravity",
            "note_type": "progress",
            "content": "Código do router e service implementados.",
        },
        headers=headers,
    )
    assert note_res.status_code == 201
    assert note_res.json()["author"] == "antigravity"

    # 9. Concluir tarefa com verificação estrita aprovada (echo Success)
    complete_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}/complete",
        json={"summary": "Funcionalidade entregue com sucesso", "execute_verification": True},
        headers=headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # 10. Excluir tarefa (requer ADMIN)
    del_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # 11. Verificar que retorna 404 após exclusão
    get_del = await client.get(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}",
        headers=headers,
    )
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_dev_tasks_strict_verification_guardrail(client: AsyncClient) -> None:
    # 1. Registrar usuário e obter token
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "guardrail_tester@softforge.com",
            "password": "Password123!",
            "full_name": "Guardrail Tester",
        },
    )
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "guardrail_tester@softforge.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. Criar workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Guardrail Test Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 3. Criar tarefa com comando que propositalmente falha
    cmd_fail = "cmd.exe /c exit 1" if sys.platform == "win32" else "exit 1"
    task_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks",
        json={
            "title": "Tarefa com guardrail com falha",
            "verification_command": cmd_fail,
        },
        headers=headers,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 4. Tentar concluir com verificação estrita -> deve falhar com 400
    complete_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}/complete",
        json={"summary": "Tentando forçar conclusão", "execute_verification": True},
        headers=headers,
    )
    assert complete_res.status_code == 400
    assert "verificação estrita falhou" in complete_res.json()["message"].lower()

    # 5. Garantir que a tarefa NÃO foi marcada como concluída
    check_res = await client.get(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}",
        headers=headers,
    )
    assert check_res.json()["status"] != "completed"

    # 6. Reportar falha explícita via /fail
    fail_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/dev-tasks/{task_id}/fail",
        json={"reason": "Testes falharam no guardrail", "is_blocked": True, "blocker_details": "Exit code 1"},
        headers=headers,
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["status"] == "blocked"


@pytest.mark.asyncio
async def test_dev_tasks_mcp_tools(client: AsyncClient) -> None:
    # 1. Registrar usuário e criar workspace
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "mcp_tester@softforge.com",
            "password": "Password123!",
            "full_name": "MCP Tester",
        },
    )
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "mcp_tester@softforge.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "MCP Integration Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 2. Chamar ferramenta MCP create_dev_task
    create_call = await handle_tool_call(
        "create_dev_task",
        {
            "workspace_id": workspace_id,
            "title": "Tarefa criada via MCP",
            "description": "Criada pelo agente através do protocolo MCP",
            "verification_command": "echo MCP_OK",
        },
    )
    assert not create_call.get("isError")
    task_created = json.loads(create_call["content"][0]["text"])
    task_id = task_created["id"]

    # 3. Chamar ferramenta MCP claim_dev_task
    claim_call = await handle_tool_call(
        "claim_dev_task",
        {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "agent_name": "claude-code",
        },
    )
    assert not claim_call.get("isError")
    claimed_task = json.loads(claim_call["content"][0]["text"])
    assert claimed_task["status"] == "in_progress"

    # 4. Chamar ferramenta MCP log_dev_task_progress
    note_call = await handle_tool_call(
        "log_dev_task_progress",
        {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "content": "Progresso registrado via MCP",
            "author": "claude-code",
        },
    )
    assert not note_call.get("isError")

    # 5. Chamar ferramenta MCP complete_dev_task
    complete_call = await handle_tool_call(
        "complete_dev_task",
        {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "summary": "Finalizado via MCP",
        },
    )
    assert not complete_call.get("isError")
    completed_task = json.loads(complete_call["content"][0]["text"])
    assert completed_task["status"] == "completed"
