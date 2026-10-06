import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole
from src.slices.workspaces.schemas import (
    AddMemberRequest,
    WorkspaceCreate,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from src.slices.workspaces.service import (
    add_workspace_member,
    create_workspace,
    get_workspace,
    list_user_workspaces,
    list_workspace_members,
    remove_workspace_member,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces & Multi-tenancy"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo workspace",
    description="Cria uma nova organização/tenant onde o usuário criador torna-se Owner.",
)
async def create(
    req: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    return await create_workspace(session, current_user.id, req)


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    summary="Listar workspaces do usuário",
    description="Retorna todos os workspaces aos quais o usuário autenticado pertence.",
)
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[WorkspaceResponse]:
    return await list_user_workspaces(session, current_user.id)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Obter detalhes de um workspace",
    description="Retorna os dados do workspace. Requer permissão mínima de Viewer.",
)
async def get_workspace_details(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    ws = await get_workspace(session, workspace_id)
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        slug=ws.slug,
        owner_id=ws.owner_id,
        role=membership.role,
        created_at=ws.created_at,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
    summary="Listar membros do workspace",
    description="Lista todos os usuários que fazem parte deste workspace. Requer permissão de Viewer.",
)
async def get_members(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[WorkspaceMemberResponse]:
    _ = membership
    return await list_workspace_members(session, workspace_id)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar membro ao workspace",
    description="Convida/adiciona um usuário existente com uma role específica. Requer permissão mínima de Admin.",
)
async def add_member(
    workspace_id: uuid.UUID,
    req: AddMemberRequest,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceMemberResponse:
    _ = membership
    return await add_workspace_member(session, workspace_id, req)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover membro do workspace",
    description="Remove o acesso de um usuário ao workspace. Requer permissão mínima de Admin.",
)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    _ = membership
    await remove_workspace_member(session, workspace_id, user_id)
