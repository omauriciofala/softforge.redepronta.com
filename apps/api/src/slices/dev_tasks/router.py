import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.dev_tasks.schemas import (
    DevTaskClaim,
    DevTaskComplete,
    DevTaskCreate,
    DevTaskFail,
    DevTaskListResponse,
    DevTaskNoteCreate,
    DevTaskNoteResponse,
    DevTaskResponse,
    DevTaskUpdate,
)
from src.slices.dev_tasks.service import (
    add_dev_task_note,
    claim_dev_task,
    complete_dev_task,
    create_dev_task,
    delete_dev_task,
    fail_dev_task,
    get_dev_task,
    list_dev_tasks,
    update_dev_task,
)
from src.slices.webhooks.service import trigger_webhook_event
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/dev-tasks", tags=["Tarefas de Desenvolvimento (DevTasks)"])


@router.post("", response_model=DevTaskResponse, status_code=status.HTTP_201_CREATED)
async def create(
    workspace_id: uuid.UUID,
    req: DevTaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> DevTaskResponse:
    _ = membership
    task = await create_dev_task(session, workspace_id, req, created_by_id=current_user.id)
    await log_audit_event(
        action="dev_task.created",
        resource_type="dev_task",
        resource_id=str(task.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="dev_task.created",
        payload={
            "task_id": str(task.id),
            "title": task.title,
            "task_type": task.task_type,
            "priority": task.priority,
            "status": task.status,
            "workspace_id": str(workspace_id),
        },
    )
    return DevTaskResponse.model_validate(task)


@router.get("", response_model=DevTaskListResponse)
async def list_all(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
    task_status: str | None = Query(default=None, alias="status", description="Filtrar por status"),
    priority: str | None = Query(default=None, description="Filtrar por prioridade"),
    project_id: uuid.UUID | None = Query(default=None, description="Filtrar por ID do projeto"),
    limit: int = Query(default=50, ge=1, le=100, description="Quantidade por página"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginação"),
) -> DevTaskListResponse:
    _ = membership
    items, total = await list_dev_tasks(
        session=session,
        workspace_id=workspace_id,
        status=task_status,
        priority=priority,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return DevTaskListResponse(
        items=[DevTaskResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/{task_id}", response_model=DevTaskResponse)
async def get_by_id(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskResponse:
    _ = membership
    task = await get_dev_task(session, workspace_id, task_id)
    return DevTaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=DevTaskResponse)
async def update(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskUpdate,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskResponse:
    _ = membership
    task = await update_dev_task(session, workspace_id, task_id, req)
    return DevTaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    _ = membership
    await delete_dev_task(session, workspace_id, task_id)


@router.post("/{task_id}/claim", response_model=DevTaskResponse)
async def claim(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskClaim,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskResponse:
    _ = membership
    task = await claim_dev_task(session, workspace_id, task_id, req.agent_name)
    return DevTaskResponse.model_validate(task)


@router.post("/{task_id}/notes", response_model=DevTaskNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskNoteCreate,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskNoteResponse:
    _ = membership
    note = await add_dev_task_note(session, workspace_id, task_id, req)
    return DevTaskNoteResponse.model_validate(note)


@router.post("/{task_id}/complete", response_model=DevTaskResponse)
async def complete(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskComplete,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskResponse:
    _ = membership
    task = await complete_dev_task(
        session=session,
        workspace_id=workspace_id,
        task_id=task_id,
        summary=req.summary,
        execute_verification=req.execute_verification,
    )
    return DevTaskResponse.model_validate(task)


@router.post("/{task_id}/fail", response_model=DevTaskResponse)
async def fail(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DevTaskFail,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DevTaskResponse:
    _ = membership
    task = await fail_dev_task(
        session=session,
        workspace_id=workspace_id,
        task_id=task_id,
        reason=req.reason,
        is_blocked=req.is_blocked,
        blocker_details=req.blocker_details,
    )
    return DevTaskResponse.model_validate(task)
