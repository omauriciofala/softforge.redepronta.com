import asyncio
import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, NotFoundException
from src.core.security import get_password_hash
from src.slices.auth.models import User
from src.slices.dev_tasks.models import (
    DevTask,
    DevTaskNote,
    DevTaskNoteType,
    DevTaskStatus,
)
from src.slices.dev_tasks.schemas import (
    DevTaskCreate,
    DevTaskNoteCreate,
    DevTaskUpdate,
)
from src.slices.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole


async def create_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    req: DevTaskCreate,
    created_by_id: uuid.UUID | None = None,
) -> DevTask:
    task = DevTask(
        workspace_id=workspace_id,
        project_id=req.project_id,
        title=req.title,
        description=req.description,
        task_type=req.task_type.value,
        priority=req.priority.value,
        status=DevTaskStatus.TODO.value,
        target_files=req.target_files,
        acceptance_criteria=req.acceptance_criteria,
        verification_command=req.verification_command,
        git_branch=req.git_branch,
        assigned_agent=req.assigned_agent,
        created_by_id=created_by_id,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def list_dev_tasks(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    status: str | None = None,
    priority: str | None = None,
    project_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[DevTask], int]:
    base_stmt = select(DevTask).where(DevTask.workspace_id == workspace_id)
    count_stmt = select(func.count(DevTask.id)).where(DevTask.workspace_id == workspace_id)

    if status:
        base_stmt = base_stmt.where(DevTask.status == status)
        count_stmt = count_stmt.where(DevTask.status == status)
    if priority:
        base_stmt = base_stmt.where(DevTask.priority == priority)
        count_stmt = count_stmt.where(DevTask.priority == priority)
    if project_id:
        base_stmt = base_stmt.where(DevTask.project_id == project_id)
        count_stmt = count_stmt.where(DevTask.project_id == project_id)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = (
        base_stmt.order_by(DevTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return tasks, total


async def get_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
) -> DevTask:
    stmt = select(DevTask).where(
        DevTask.id == task_id,
        DevTask.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(message="Tarefa de desenvolvimento não encontrada.")
    return task


async def update_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskUpdate,
) -> DevTask:
    task = await get_dev_task(session, workspace_id, task_id)

    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.project_id is not None:
        task.project_id = req.project_id
    if req.task_type is not None:
        task.task_type = req.task_type.value
    if req.priority is not None:
        task.priority = req.priority.value
    if req.status is not None:
        task.status = req.status.value
    if req.target_files is not None:
        task.target_files = req.target_files
    if req.acceptance_criteria is not None:
        task.acceptance_criteria = req.acceptance_criteria
    if req.verification_command is not None:
        task.verification_command = req.verification_command
    if req.git_branch is not None:
        task.git_branch = req.git_branch
    if req.assigned_agent is not None:
        task.assigned_agent = req.assigned_agent

    await session.flush()
    await session.refresh(task)
    return task


async def delete_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
) -> None:
    task = await get_dev_task(session, workspace_id, task_id)
    await session.delete(task)
    await session.flush()


async def claim_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    agent_name: str,
) -> DevTask:
    task = await get_dev_task(session, workspace_id, task_id)
    task.assigned_agent = agent_name
    task.status = DevTaskStatus.IN_PROGRESS.value

    note = DevTaskNote(
        task_id=task.id,
        author=agent_name,
        note_type=DevTaskNoteType.PROGRESS.value,
        content=f"Tarefa assumida pelo agente '{agent_name}'.",
    )
    session.add(note)
    await session.flush()
    await session.refresh(task)
    return task


async def add_dev_task_note(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskNoteCreate,
) -> DevTaskNote:
    task = await get_dev_task(session, workspace_id, task_id)
    note = DevTaskNote(
        task_id=task.id,
        author=req.author,
        note_type=req.note_type.value,
        content=req.content,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)
    return note


async def complete_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    summary: str,
    execute_verification: bool = True,
) -> DevTask:
    task = await get_dev_task(session, workspace_id, task_id)

    # Execução estrita do comando de verificação se configurado
    if task.verification_command and execute_verification:
        try:
            proc = await asyncio.create_subprocess_shell(
                task.verification_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            output_text = stdout.decode("utf-8", errors="replace")
        except Exception as exc:
            output_text = f"Erro ao invocar subprocesso de verificação: {exc}"
            task.verification_output = output_text
            note = DevTaskNote(
                task_id=task.id,
                author="System/Guardrail",
                note_type=DevTaskNoteType.VERIFICATION.value,
                content=output_text,
            )
            session.add(note)
            await session.flush()
            raise AppException(
                message=f"Falha na invocação da verificação: {exc}",
                status_code=400,
            ) from exc

        task.verification_output = output_text

        if proc.returncode != 0:
            note = DevTaskNote(
                task_id=task.id,
                author="System/Guardrail",
                note_type=DevTaskNoteType.VERIFICATION.value,
                content=f"Verificação estrita FALHOU (código {proc.returncode}):\n{output_text[:1000]}",
            )
            session.add(note)
            await session.flush()
            raise AppException(
                message=f"A verificação estrita falhou com código de retorno {proc.returncode}. A tarefa não pode ser concluída sem aprovação dos testes/guardrails.",
                status_code=400,
                details={"exit_code": proc.returncode, "output_preview": output_text[:500]},
            )

        # Verificação aprovada
        note_success = DevTaskNote(
            task_id=task.id,
            author="System/Guardrail",
            note_type=DevTaskNoteType.VERIFICATION.value,
            content=f"Verificação estrita APROVADA (código 0):\n{output_text[:500]}",
        )
        session.add(note_success)

    task.status = DevTaskStatus.COMPLETED.value
    author = task.assigned_agent or "Agent"
    note_done = DevTaskNote(
        task_id=task.id,
        author=author,
        note_type=DevTaskNoteType.DECISION.value,
        content=f"Tarefa concluída com sucesso: {summary}",
    )
    session.add(note_done)

    await session.flush()
    await session.refresh(task)
    return task


async def fail_dev_task(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    reason: str,
    is_blocked: bool = False,
    blocker_details: str | None = None,
) -> DevTask:
    task = await get_dev_task(session, workspace_id, task_id)
    new_status = DevTaskStatus.BLOCKED.value if is_blocked else DevTaskStatus.FAILED.value
    task.status = new_status

    author = task.assigned_agent or "Agent"
    note_type = DevTaskNoteType.BLOCKER.value if is_blocked else DevTaskNoteType.DECISION.value
    content = f"{'Impedimento reportado' if is_blocked else 'Falha técnica'}: {reason}"
    if blocker_details:
        content += f"\nDetalhes adicionais: {blocker_details}"

    note = DevTaskNote(
        task_id=task.id,
        author=author,
        note_type=note_type,
        content=content,
    )
    session.add(note)
    await session.flush()
    await session.refresh(task)
    return task


async def ensure_default_workspace(session: AsyncSession) -> uuid.UUID:
    """Descobre o primeiro workspace ativo ou inicializa um workspace de desenvolvimento padrão."""
    stmt = select(Workspace).order_by(Workspace.created_at.asc())
    result = await session.execute(stmt)
    ws = result.scalars().first()
    if ws:
        return ws.id

    # Busca ou cria usuário padrão do sistema
    user_stmt = select(User).order_by(User.created_at.asc())
    user_result = await session.execute(user_stmt)
    user = user_result.scalars().first()
    if not user:
        user = User(
            email="dev@softforge.com",
            full_name="SoftForge Developer",
            hashed_password=get_password_hash("Password123!"),
            is_active=True,
            is_superuser=True,
        )
        session.add(user)
        await session.flush()

    new_ws = Workspace(
        name="Dev Workspace",
        slug=f"dev-workspace-{uuid.uuid4().hex[:6]}",
        owner_id=user.id,
    )
    session.add(new_ws)
    await session.flush()

    member = WorkspaceMember(
        workspace_id=new_ws.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    session.add(member)
    await session.flush()

    return new_ws.id
