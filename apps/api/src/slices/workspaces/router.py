import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.webhooks.service import trigger_webhook_event
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole
from src.slices.workspaces.schemas import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
    WorkspaceCreate,
    WorkspaceInviteAcceptRequest,
    WorkspaceInviteCreate,
    WorkspaceInviteListResponse,
    WorkspaceInviteResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from src.slices.workspaces.service import (
    accept_workspace_invite,
    add_workspace_member,
    create_workspace,
    create_workspace_invite,
    get_workspace,
    list_user_workspaces,
    list_workspace_invites,
    list_workspace_members,
    remove_workspace_member,
    revoke_workspace_invite,
    update_workspace_member_role,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces, Equipes & RBAC"])


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
    request: Request = None,
) -> WorkspaceResponse:
    ws = await create_workspace(session, current_user.id, req)
    await log_audit_event(
        action="workspace.created",
        resource_type="workspace",
        resource_id=str(ws.id),
        workspace_id=ws.id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    return ws


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


@router.post(
    "/invites/accept",
    response_model=WorkspaceResponse,
    summary="Aceitar convite de equipe",
    description="Permite que o usuário autenticado utilize um token de convite válido para ingressar em um workspace.",
)
async def accept_invite(
    req: WorkspaceInviteAcceptRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> WorkspaceResponse:
    ws, member = await accept_workspace_invite(session, req.token, current_user)

    await log_audit_event(
        action="invite.accepted",
        resource_type="workspace_invite",
        resource_id=str(ws.id),
        workspace_id=ws.id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=ws.id,
        event_type="member.joined",
        payload={
            "workspace_id": str(ws.id),
            "user_id": str(current_user.id),
            "email": current_user.email,
            "role": member.role.value,
        },
    )

    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        slug=ws.slug,
        owner_id=ws.owner_id,
        role=member.role,
        created_at=ws.created_at,
    )


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
    summary="Adicionar membro direto ao workspace",
    description="Adiciona diretamente um usuário existente com uma role específica. Requer permissão de Admin.",
)
async def add_member(
    workspace_id: uuid.UUID,
    req: AddMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> WorkspaceMemberResponse:
    _ = membership
    member = await add_workspace_member(session, workspace_id, req)

    await log_audit_event(
        action="member.added",
        resource_type="workspace_member",
        resource_id=str(member.user_id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="member.joined",
        payload={
            "workspace_id": str(workspace_id),
            "user_id": str(member.user_id),
            "email": member.email,
            "role": member.role.value,
        },
    )

    return member


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Alterar cargo de membro do workspace",
    description="Atualiza a role RBAC de um membro no workspace. Requer permissão mínima de Admin.",
)
async def update_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    req: UpdateMemberRoleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> WorkspaceMemberResponse:
    _ = membership
    member = await update_workspace_member_role(session, workspace_id, user_id, req, current_user)

    await log_audit_event(
        action="member.role_updated",
        resource_type="workspace_member",
        resource_id=str(user_id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="member.role_updated",
        payload={
            "workspace_id": str(workspace_id),
            "user_id": str(user_id),
            "new_role": member.role.value,
            "updated_by": str(current_user.id),
        },
    )

    return member


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover membro do workspace",
    description="Remove o acesso de um usuário ao workspace. Requer permissão mínima de Admin.",
)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> None:
    _ = membership
    await remove_workspace_member(session, workspace_id, user_id)

    await log_audit_event(
        action="member.removed",
        resource_type="workspace_member",
        resource_id=str(user_id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="member.removed",
        payload={
            "workspace_id": str(workspace_id),
            "user_id": str(user_id),
            "removed_by": str(current_user.id),
        },
    )


# --- Endpoints de Convites de Equipe (Invites) ---


@router.post(
    "/{workspace_id}/invites",
    response_model=WorkspaceInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar convite de equipe por e-mail",
    description="Gera um token seguro de 7 dias e despacha notificação por e-mail via Arq Worker. Requer permissão de Admin.",
)
async def create_invite(
    workspace_id: uuid.UUID,
    req: WorkspaceInviteCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> WorkspaceInviteResponse:
    _ = membership
    invite = await create_workspace_invite(session, workspace_id, current_user, req)

    await log_audit_event(
        action="invite.created",
        resource_type="workspace_invite",
        resource_id=str(invite.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="member.invited",
        payload={
            "workspace_id": str(workspace_id),
            "invite_id": str(invite.id),
            "email": invite.email,
            "role": invite.role.value,
            "invited_by": str(current_user.id),
        },
    )

    return WorkspaceInviteResponse.model_validate(invite)


@router.get(
    "/{workspace_id}/invites",
    response_model=WorkspaceInviteListResponse,
    summary="Listar convites pendentes do workspace",
    description="Retorna todos os convites ativos que ainda não foram aceitos nem revogados. Requer permissão de Admin.",
)
async def list_invites(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceInviteListResponse:
    _ = membership
    invites = await list_workspace_invites(session, workspace_id)
    return WorkspaceInviteListResponse(
        items=[WorkspaceInviteResponse.model_validate(i) for i in invites],
        total=len(invites),
    )


@router.delete(
    "/{workspace_id}/invites/{invite_id}",
    response_model=WorkspaceInviteResponse,
    summary="Revogar convite de equipe",
    description="Invalida imediatamente o token do convite. Requer permissão mínima de Admin.",
)
async def revoke_invite(
    workspace_id: uuid.UUID,
    invite_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> WorkspaceInviteResponse:
    _ = membership
    invite = await revoke_workspace_invite(session, workspace_id, invite_id)

    await log_audit_event(
        action="invite.revoked",
        resource_type="workspace_invite",
        resource_id=str(invite.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    return WorkspaceInviteResponse.model_validate(invite)
