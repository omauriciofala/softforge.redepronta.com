"""Servidor MCP (Model Context Protocol) nativo para gestão de DevTasks no SoftForge.

Implementa JSON-RPC 2.0 sobre stdio com zero dependências externas, compatível
com Google Antigravity, Claude Code, Cursor e Windsurf.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Any

from src.config import settings
from src.core.database import AsyncSessionLocal, Base, discover_and_import_models, engine
from src.slices.dev_tasks.models import (
    DevTaskNoteType,
    DevTaskPriority,
    DevTaskType,
)
from src.slices.dev_tasks.schemas import (
    DevTaskCreate,
    DevTaskNoteCreate,
    DevTaskResponse,
)
from src.slices.dev_tasks.service import (
    add_dev_task_note,
    claim_dev_task,
    complete_dev_task,
    create_dev_task,
    ensure_default_workspace,
    fail_dev_task,
    get_dev_task,
    list_dev_tasks,
)

# Silencia logs de SQLAlchemy no stdout para não corromper o protocolo JSON-RPC do MCP
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

SERVER_NAME = "softforge-dev-tasks"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"


async def init_local_database_if_needed() -> None:
    """Garante tabelas criadas localmente no SQLite caso o servidor não esteja ativo."""
    engine.echo = False
    if "sqlite" in settings.DATABASE_URL:
        discover_and_import_models()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def resolve_target_workspace_id(session: Any, explicit_id: str | None = None) -> uuid.UUID:
    """Resolve o workspace pelo argumento, variável de ambiente ou fallback automático."""
    if explicit_id:
        return uuid.UUID(explicit_id)

    env_ws = os.getenv("SOFTFORGE_WORKSPACE_ID")
    if env_ws:
        return uuid.UUID(env_ws)

    return await ensure_default_workspace(session)


# Catálogo de Ferramentas MCP
TOOLS_DEFINITIONS = [
    {
        "name": "list_dev_tasks",
        "description": "Lista tarefas de desenvolvimento registradas no SoftForge com filtros opcionais.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "review", "completed", "failed", "blocked", "cancelled"],
                    "description": "Filtrar por status",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Filtrar por prioridade",
                },
                "workspace_id": {
                    "type": "string",
                    "description": "UUID do workspace (opcional, detectado automaticamente se omitido)",
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Limite máximo de tarefas a retornar",
                },
            },
        },
    },
    {
        "name": "get_dev_task",
        "description": "Obtém todos os detalhes técnicos, critérios de aceite e notas de progresso de uma tarefa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID da tarefa de desenvolvimento",
                },
                "workspace_id": {
                    "type": "string",
                    "description": "UUID do workspace (opcional)",
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "create_dev_task",
        "description": "Cria uma nova tarefa de desenvolvimento ou decompõe requisitos em subtarefas técnicas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título conciso da tarefa"},
                "description": {"type": "string", "description": "Objetivo, contexto e instruções para implementação"},
                "task_type": {
                    "type": "string",
                    "enum": ["feature", "bugfix", "refactor", "test", "doc", "chore"],
                    "default": "feature",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "default": "medium",
                },
                "target_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de arquivos impactados ou alvo",
                },
                "acceptance_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Checklist de critérios de aceite",
                },
                "verification_command": {
                    "type": "string",
                    "description": "Comando a ser executado para verificar a tarefa (ex: 'pytest ...')",
                },
                "git_branch": {"type": "string", "description": "Branch git associada"},
                "assigned_agent": {"type": "string", "description": "Identificador do agente alocado"},
                "workspace_id": {"type": "string", "description": "UUID do workspace (opcional)"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "claim_dev_task",
        "description": "Assume a execução de uma tarefa por um agente de IA, alterando seu status para 'in_progress'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "UUID da tarefa"},
                "agent_name": {"type": "string", "description": "Nome ou identificador do agente (ex: 'antigravity')"},
                "workspace_id": {"type": "string", "description": "UUID do workspace (opcional)"},
            },
            "required": ["task_id", "agent_name"],
        },
    },
    {
        "name": "log_dev_task_progress",
        "description": "Registra notas de progresso, decisões arquiteturais ou bloqueios encontrados durante o desenvolvimento.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "UUID da tarefa"},
                "content": {"type": "string", "description": "Texto da anotação de progresso ou decisão"},
                "author": {"type": "string", "default": "agent", "description": "Autor da nota"},
                "note_type": {
                    "type": "string",
                    "enum": ["progress", "decision", "blocker", "verification"],
                    "default": "progress",
                },
                "workspace_id": {"type": "string", "description": "UUID do workspace (opcional)"},
            },
            "required": ["task_id", "content"],
        },
    },
    {
        "name": "complete_dev_task",
        "description": "Conclui a tarefa de desenvolvimento. Executa estritamente o comando de verificação configurado e exige retorno código 0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "UUID da tarefa"},
                "summary": {"type": "string", "description": "Resumo das alterações realizadas e justificativa"},
                "execute_verification": {
                    "type": "boolean",
                    "default": True,
                    "description": "Executa o comando de teste/guardrail configurado antes de concluir",
                },
                "workspace_id": {"type": "string", "description": "UUID do workspace (opcional)"},
            },
            "required": ["task_id", "summary"],
        },
    },
    {
        "name": "fail_dev_task",
        "description": "Reporta falha técnica ou impedimento irrecuperável na tarefa, alterando status para 'blocked' ou 'failed'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "UUID da tarefa"},
                "reason": {"type": "string", "description": "Motivo da falha ou impedimento"},
                "is_blocked": {
                    "type": "boolean",
                    "default": False,
                    "description": "Se verdadeiro, marca como 'blocked'; se falso, marca como 'failed'",
                },
                "blocker_details": {"type": "string", "description": "Detalhes técnicos adicionais ou stack trace"},
                "workspace_id": {"type": "string", "description": "UUID do workspace (opcional)"},
            },
            "required": ["task_id", "reason"],
        },
    },
]


async def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Executa a ferramenta MCP chamada pelo agente interagindo diretamente com o serviço."""
    await init_local_database_if_needed()

    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, arguments.get("workspace_id"))

        if tool_name == "list_dev_tasks":
            tasks, total = await list_dev_tasks(
                session=session,
                workspace_id=ws_id,
                status=arguments.get("status"),
                priority=arguments.get("priority"),
                limit=arguments.get("limit", 20),
            )
            payload = [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "task_type": t.task_type,
                    "assigned_agent": t.assigned_agent,
                    "verification_command": t.verification_command,
                }
                for t in tasks
            ]
            await session.commit()
            return {"content": [{"type": "text", "text": json.dumps({"tasks": payload, "total": total}, indent=2)}]}

        elif tool_name == "get_dev_task":
            task_id = uuid.UUID(arguments["task_id"])
            task = await get_dev_task(session, ws_id, task_id)
            task_dict = DevTaskResponse.model_validate(task).model_dump(mode="json")
            await session.commit()
            return {"content": [{"type": "text", "text": json.dumps(task_dict, indent=2)}]}

        elif tool_name == "create_dev_task":
            req = DevTaskCreate(
                title=arguments["title"],
                description=arguments.get("description"),
                task_type=DevTaskType(arguments.get("task_type", "feature")),
                priority=DevTaskPriority(arguments.get("priority", "medium")),
                target_files=arguments.get("target_files") or [],
                acceptance_criteria=arguments.get("acceptance_criteria") or [],
                verification_command=arguments.get("verification_command"),
                git_branch=arguments.get("git_branch"),
                assigned_agent=arguments.get("assigned_agent"),
            )
            task = await create_dev_task(session, ws_id, req)
            task_dict = DevTaskResponse.model_validate(task).model_dump(mode="json")
            await session.commit()
            return {"content": [{"type": "text", "text": json.dumps(task_dict, indent=2)}]}

        elif tool_name == "claim_dev_task":
            task_id = uuid.UUID(arguments["task_id"])
            agent_name = arguments["agent_name"]
            task = await claim_dev_task(session, ws_id, task_id, agent_name)
            task_dict = DevTaskResponse.model_validate(task).model_dump(mode="json")
            await session.commit()
            return {"content": [{"type": "text", "text": json.dumps(task_dict, indent=2)}]}

        elif tool_name == "log_dev_task_progress":
            task_id = uuid.UUID(arguments["task_id"])
            req = DevTaskNoteCreate(
                author=arguments.get("author", "agent"),
                note_type=DevTaskNoteType(arguments.get("note_type", "progress")),
                content=arguments["content"],
            )
            note = await add_dev_task_note(session, ws_id, task_id, req)
            await session.commit()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Nota registrada com sucesso (ID: {note.id}) para a tarefa {task_id}.",
                    }
                ]
            }

        elif tool_name == "complete_dev_task":
            task_id = uuid.UUID(arguments["task_id"])
            summary = arguments["summary"]
            execute_verification = arguments.get("execute_verification", True)

            try:
                task = await complete_dev_task(
                    session=session,
                    workspace_id=ws_id,
                    task_id=task_id,
                    summary=summary,
                    execute_verification=execute_verification,
                )
                await session.commit()
                task_dict = DevTaskResponse.model_validate(task).model_dump(mode="json")
                return {"content": [{"type": "text", "text": json.dumps(task_dict, indent=2)}]}
            except Exception as exc:
                await session.commit()  # Salva anotações de falha se houver
                return {
                    "content": [{"type": "text", "text": f"Erro de verificação ou conclusão: {exc}"}],
                    "isError": True,
                }

        elif tool_name == "fail_dev_task":
            task_id = uuid.UUID(arguments["task_id"])
            reason = arguments["reason"]
            is_blocked = arguments.get("is_blocked", False)
            blocker_details = arguments.get("blocker_details")
            task = await fail_dev_task(
                session=session,
                workspace_id=ws_id,
                task_id=task_id,
                reason=reason,
                is_blocked=is_blocked,
                blocker_details=blocker_details,
            )
            await session.commit()
            task_dict = DevTaskResponse.model_validate(task).model_dump(mode="json")
            return {"content": [{"type": "text", "text": json.dumps(task_dict, indent=2)}]}

        else:
            return {
                "content": [{"type": "text", "text": f"Ferramenta desconhecida: '{tool_name}'"}],
                "isError": True,
            }


async def run_mcp_server() -> None:
    """Loop principal de leitura de comandos JSON-RPC 2.0 sobre stdin/stdout."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line_bytes = await reader.readline()
        if not line_bytes:
            break

        line = line_bytes.decode("utf-8").strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            }
        elif method == "notifications/initialized":
            continue  # Notificação sem resposta
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_DEFINITIONS},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                call_result = await handle_tool_call(tool_name, arguments)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": call_result}
            except Exception as exc:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Erro interno ao executar {tool_name}: {exc}"}],
                        "isError": True,
                    },
                }
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Método não encontrado: '{method}'"},
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
