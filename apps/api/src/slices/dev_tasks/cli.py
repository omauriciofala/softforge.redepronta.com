"""CLI para gestão de tarefas de desenvolvimento (DevTasks) no SoftForge.

Permite manipulação direta pelo desenvolvedor ou por agentes de IA via terminal,
conectando diretamente ao banco local (SQLite/PostgreSQL) sem depender do servidor FastAPI estar rodando.
"""

import argparse
import asyncio
import json
import logging
import sys
import uuid

from src.config import settings
from src.core.database import AsyncSessionLocal, Base, discover_and_import_models, engine
from src.slices.dev_tasks.mcp import main as mcp_main
from src.slices.dev_tasks.mcp import resolve_target_workspace_id
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
    fail_dev_task,
    get_dev_task,
    list_dev_tasks,
)

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


async def init_db() -> None:
    engine.echo = False
    if "sqlite" in settings.DATABASE_URL:
        discover_and_import_models()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def cmd_list(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        tasks, total = await list_dev_tasks(
            session=session,
            workspace_id=ws_id,
            status=args.status,
            priority=args.priority,
            limit=args.limit,
        )
        if args.json:
            out = [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "task_type": t.task_type,
                    "assigned_agent": t.assigned_agent,
                }
                for t in tasks
            ]
            print(json.dumps({"tasks": out, "total": total}, indent=2, ensure_ascii=False))
        else:
            print(f"\n📋 Tarefas de Desenvolvimento (Total: {total} | Workspace: {ws_id}):")
            print("=" * 80)
            if not tasks:
                print("  Nenhuma tarefa encontrada para os critérios selecionados.")
            for t in tasks:
                agent = f"[{t.assigned_agent}]" if t.assigned_agent else "[Não atribuído]"
                print(f"• ID: {t.id} | [{t.status.upper()}] ({t.priority}) {agent}")
                print(f"  Título: {t.title}")
                if t.verification_command:
                    print(f"  Comando Verificação: {t.verification_command}")
                print("-" * 80)
        await session.commit()


async def cmd_get(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        task_id = uuid.UUID(args.task_id)
        task = await get_dev_task(session, ws_id, task_id)
        data = DevTaskResponse.model_validate(task).model_dump(mode="json")
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n🔍 Detalhes da Tarefa: {data['title']}")
            print("=" * 80)
            print(f"ID:           {data['id']}")
            print(f"Status:       {data['status'].upper()}")
            print(f"Tipo:         {data['task_type']}")
            print(f"Prioridade:   {data['priority']}")
            print(f"Agente:       {data['assigned_agent'] or 'Nenhum'}")
            print(f"Branch:       {data['git_branch'] or 'N/A'}")
            print(f"Descrição:    {data['description'] or 'Sem descrição'}")
            if data["target_files"]:
                print(f"Arquivos:     {', '.join(data['target_files'])}")
            if data["acceptance_criteria"]:
                print("Critérios de Aceite:")
                for c in data["acceptance_criteria"]:
                    print(f"  - [ ] {c}")
            if data["verification_command"]:
                print(f"Verificação:  {data['verification_command']}")
            if data["notes"]:
                print("\nNotas e Progresso:")
                for n in data["notes"]:
                    print(f"  [{n['created_at'][:19]}] {n['author']} ({n['note_type']}): {n['content']}")
            print("=" * 80)
        await session.commit()


async def cmd_create(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        target_files = [f.strip() for f in args.target_files.split(",")] if args.target_files else []
        criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else []

        req = DevTaskCreate(
            title=args.title,
            description=args.description,
            task_type=DevTaskType(args.task_type),
            priority=DevTaskPriority(args.priority),
            target_files=target_files,
            acceptance_criteria=criteria,
            verification_command=args.verify_cmd,
            git_branch=args.branch,
            assigned_agent=args.agent,
        )
        task = await create_dev_task(session, ws_id, req)
        await session.commit()
        if args.json:
            print(json.dumps(DevTaskResponse.model_validate(task).model_dump(mode="json"), indent=2, ensure_ascii=False))
        else:
            print("✨ Tarefa criada com sucesso!")
            print(f"ID: {task.id}")
            print(f"Título: {task.title}")


async def cmd_claim(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        task_id = uuid.UUID(args.task_id)
        _ = await claim_dev_task(session, ws_id, task_id, args.agent)
        await session.commit()
        print(f"🤖 Tarefa {task_id} assumida com sucesso pelo agente '{args.agent}'. Status: in_progress")


async def cmd_note(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        task_id = uuid.UUID(args.task_id)
        req = DevTaskNoteCreate(
            author=args.author,
            note_type=DevTaskNoteType(args.type),
            content=args.content,
        )
        note = await add_dev_task_note(session, ws_id, task_id, req)
        await session.commit()
        print(f"📝 Anotação (ID: {note.id}) adicionada com sucesso à tarefa {task_id}.")


async def cmd_complete(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        task_id = uuid.UUID(args.task_id)
        execute_verification = not args.no_verify

        print(f"⏳ Finalizando tarefa {task_id} (Verificação estrita: {execute_verification})...")
        try:
            task = await complete_dev_task(
                session=session,
                workspace_id=ws_id,
                task_id=task_id,
                summary=args.summary,
                execute_verification=execute_verification,
            )
            await session.commit()
            print(f"✅ Tarefa {task_id} concluída com sucesso! Status: {task.status}")
        except Exception as exc:
            await session.commit()
            print(f"❌ Falha ao concluir tarefa: {exc}", file=sys.stderr)
            sys.exit(1)


async def cmd_fail(args: argparse.Namespace) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        ws_id = await resolve_target_workspace_id(session, args.workspace_id)
        task_id = uuid.UUID(args.task_id)
        _ = await fail_dev_task(
            session=session,
            workspace_id=ws_id,
            task_id=task_id,
            reason=args.reason,
            is_blocked=args.blocked,
            blocker_details=args.details,
        )
        await session.commit()
        status_label = "BLOCKED" if args.blocked else "FAILED"
        print(f"⚠️ Tarefa {task_id} marcada como {status_label}. Motivo: {args.reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev_tasks",
        description="SoftForge DevTasks — Gestor de tarefas de desenvolvimento para agentes de IA e desenvolvedores",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="Listar tarefas de desenvolvimento")
    p_list.add_argument("--status", choices=["todo", "in_progress", "review", "completed", "failed", "blocked", "cancelled"])
    p_list.add_argument("--priority", choices=["low", "medium", "high", "urgent"])
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--workspace-id", help="UUID do workspace (opcional)")
    p_list.add_argument("--json", action="store_true", help="Saída em formato JSON")

    # get
    p_get = subparsers.add_parser("get", help="Obter detalhes de uma tarefa")
    p_get.add_argument("task_id", help="UUID da tarefa")
    p_get.add_argument("--workspace-id", help="UUID do workspace (opcional)")
    p_get.add_argument("--json", action="store_true", help="Saída em formato JSON")

    # create
    p_create = subparsers.add_parser("create", help="Criar nova tarefa")
    p_create.add_argument("--title", required=True, help="Título da tarefa")
    p_create.add_argument("--description", help="Descrição detalhada e contexto")
    p_create.add_argument("--task-type", default="feature", choices=["feature", "bugfix", "refactor", "test", "doc", "chore"])
    p_create.add_argument("--priority", default="medium", choices=["low", "medium", "high", "urgent"])
    p_create.add_argument("--target-files", help="Arquivos separados por vírgula")
    p_create.add_argument("--criteria", help="Critérios de aceite separados por vírgula")
    p_create.add_argument("--verify-cmd", help="Comando técnico de verificação (ex: pytest ...)")
    p_create.add_argument("--branch", help="Nome da branch git")
    p_create.add_argument("--agent", help="Nome do agente alocado")
    p_create.add_argument("--workspace-id", help="UUID do workspace (opcional)")
    p_create.add_argument("--json", action="store_true", help="Saída em formato JSON")

    # claim
    p_claim = subparsers.add_parser("claim", help="Agente assume a tarefa")
    p_claim.add_argument("task_id", help="UUID da tarefa")
    p_claim.add_argument("--agent", default="antigravity", help="Nome do agente")
    p_claim.add_argument("--workspace-id", help="UUID do workspace (opcional)")

    # note
    p_note = subparsers.add_parser("note", help="Adicionar nota de progresso à tarefa")
    p_note.add_argument("task_id", help="UUID da tarefa")
    p_note.add_argument("--content", required=True, help="Texto da nota")
    p_note.add_argument("--author", default="agent", help="Autor da nota")
    p_note.add_argument("--type", default="progress", choices=["progress", "decision", "blocker", "verification"])
    p_note.add_argument("--workspace-id", help="UUID do workspace (opcional)")

    # complete
    p_complete = subparsers.add_parser("complete", help="Concluir tarefa com verificação estrita")
    p_complete.add_argument("task_id", help="UUID da tarefa")
    p_complete.add_argument("--summary", required=True, help="Resumo da entrega")
    p_complete.add_argument("--no-verify", action="store_true", help="Pular execução do comando de verificação")
    p_complete.add_argument("--workspace-id", help="UUID do workspace (opcional)")

    # fail
    p_fail = subparsers.add_parser("fail", help="Reportar falha ou bloqueio na tarefa")
    p_fail.add_argument("task_id", help="UUID da tarefa")
    p_fail.add_argument("--reason", required=True, help="Motivo da falha ou bloqueio")
    p_fail.add_argument("--blocked", action="store_true", help="Marcar como 'blocked' em vez de 'failed'")
    p_fail.add_argument("--details", help="Detalhes técnicos ou stack trace")
    p_fail.add_argument("--workspace-id", help="UUID do workspace (opcional)")

    # mcp
    subparsers.add_parser("mcp", help="Executar servidor MCP JSON-RPC 2.0 sobre stdio")

    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "mcp":
        mcp_main()
    elif args.command == "list":
        asyncio.run(cmd_list(args))
    elif args.command == "get":
        asyncio.run(cmd_get(args))
    elif args.command == "create":
        asyncio.run(cmd_create(args))
    elif args.command == "claim":
        asyncio.run(cmd_claim(args))
    elif args.command == "note":
        asyncio.run(cmd_note(args))
    elif args.command == "complete":
        asyncio.run(cmd_complete(args))
    elif args.command == "fail":
        asyncio.run(cmd_fail(args))


if __name__ == "__main__":
    main()
