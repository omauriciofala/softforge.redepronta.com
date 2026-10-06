import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.billing.dependencies import check_quota
from src.slices.projects.schemas import (
    PaginatedProjectsResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
)
from src.slices.projects.service import (
    create_project,
    create_task,
    delete_project,
    get_project,
    list_project_tasks,
    list_projects,
    update_project,
)
from src.slices.webhooks.service import trigger_webhook_event
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["Projetos e Tarefas"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo projeto",
    description="Cria um novo projeto vinculado a um workspace específico. Requer permissão mínima de Membro.",
    dependencies=[Depends(check_quota("projects"))],
)
async def create(
    workspace_id: uuid.UUID,
    req: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> ProjectResponse:
    _ = membership
    project = await create_project(session, workspace_id, current_user.id, req)
    await log_audit_event(
        action="project.created",
        resource_type="project",
        resource_id=str(project.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="project.created",
        payload={
            "project_id": str(project.id),
            "name": project.name,
            "created_by": str(current_user.id),
            "workspace_id": str(workspace_id),
        },
    )
    return project


@router.get(
    "",
    response_model=PaginatedProjectsResponse,
    summary="Listar projetos do workspace",
    description="Lista projetos com suporte a paginação e busca por nome. Requer permissão mínima de Viewer.",
)
async def list_all(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, description="Termo para busca pelo nome do projeto"),
    include_archived: bool = Query(default=False, description="Incluir projetos arquivados"),
    limit: int = Query(default=20, ge=1, le=100, description="Quantidade por página"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginação"),
) -> PaginatedProjectsResponse:
    _ = membership
    return await list_projects(
        session=session,
        workspace_id=workspace_id,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Obter detalhes de um projeto",
    description="Retorna dados do projeto por ID. Requer permissão mínima de Viewer.",
)
async def get_by_id(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    _ = membership
    return await get_project(session, workspace_id, project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Atualizar dados de um projeto",
    description="Atualização parcial de nome, descrição ou status de arquivamento. Requer permissão mínima de Membro.",
)
async def update(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    req: ProjectUpdate,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    _ = membership
    return await update_project(session, workspace_id, project_id, req)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir projeto",
    description="Remove permanentemente o projeto e suas tarefas. Requer permissão mínima de Admin.",
)
async def delete_item(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    _ = membership
    await delete_project(session, workspace_id, project_id)


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar tarefa ao projeto",
    description="Cria uma nova tarefa associada a este projeto. Requer permissão mínima de Membro.",
)
async def create_project_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    req: TaskCreate,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    _ = membership
    # Garante que o projeto existe no workspace
    await get_project(session, workspace_id, project_id)
    return await create_task(session, project_id, req)


@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    summary="Listar tarefas do projeto",
    description="Retorna todas as tarefas vinculadas a este projeto. Requer permissão mínima de Viewer.",
)
async def get_project_tasks(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[TaskResponse]:
    _ = membership
    await get_project(session, workspace_id, project_id)
    return await list_project_tasks(session, project_id)
