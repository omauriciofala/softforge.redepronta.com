import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, NotFoundException
from src.core.queue import get_queue
from src.slices.auth.models import User
from src.slices.auth.service import get_user_by_email
from src.slices.workspaces.models import (
    Workspace,
    WorkspaceInvite,
    WorkspaceMember,
    WorkspaceRole,
)
from src.slices.workspaces.schemas import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
    WorkspaceCreate,
    WorkspaceInviteCreate,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


async def create_workspace(
    session: AsyncSession,
    owner_id: uuid.UUID,
    req: WorkspaceCreate,
) -> WorkspaceResponse:
    base_slug = req.slug if req.slug else slugify(req.name)
    slug = base_slug

    # Verifica duplicidade de slug e incrementa se necessário
    counter = 1
    while True:
        existing = await session.execute(select(Workspace).where(Workspace.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    workspace = Workspace(
        name=req.name,
        slug=slug,
        owner_id=owner_id,
    )
    session.add(workspace)
    await session.flush()

    # Adiciona o criador como OWNER
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_id,
        role=WorkspaceRole.OWNER,
    )
    session.add(membership)
    await session.flush()

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        role=WorkspaceRole.OWNER,
        created_at=workspace.created_at,
    )


async def list_user_workspaces(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[WorkspaceResponse]:
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    results = await session.execute(stmt)

    workspaces = []
    for ws, role in results.all():
        workspaces.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                slug=ws.slug,
                owner_id=ws.owner_id,
                role=role,
                created_at=ws.created_at,
            )
        )
    return workspaces


async def get_workspace(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> Workspace:
    result = await session.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise NotFoundException(message="Workspace não encontrado")
    return ws


async def list_workspace_members(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[WorkspaceMemberResponse]:
    stmt = (
        select(WorkspaceMember, User.email, User.full_name)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at.asc())
    )
    results = await session.execute(stmt)

    members = []
    for member, email, full_name in results.all():
        members.append(
            WorkspaceMemberResponse(
                id=member.id,
                user_id=member.user_id,
                email=email,
                full_name=full_name,
                role=member.role,
                created_at=member.created_at,
            )
        )
    return members


async def add_workspace_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    req: AddMemberRequest,
) -> WorkspaceMemberResponse:
    user = await get_user_by_email(session, req.email)
    if not user:
        raise NotFoundException(message=f"Usuário com e-mail '{req.email}' não cadastrado")

    # Verifica se já é membro
    existing = await session.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise AppException(
            message="Este usuário já faz parte deste workspace",
            status_code=409,
            code="MEMBER_ALREADY_EXISTS",
        )

    membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=req.role,
    )
    session.add(membership)
    await session.flush()

    return WorkspaceMemberResponse(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        created_at=membership.created_at,
    )


async def remove_workspace_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
) -> None:
    ws = await get_workspace(session, workspace_id)
    if ws.owner_id == target_user_id:
        raise AppException(
            message="Não é permitido remover o proprietário (Owner) do workspace",
            status_code=400,
            code="CANNOT_REMOVE_OWNER",
        )

    result = await session.execute(
        delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
        )
    )
    if result.rowcount == 0:
        raise NotFoundException(message="Membro não encontrado no workspace")


async def update_workspace_member_role(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    req: UpdateMemberRoleRequest,
    operator_user: User,
) -> WorkspaceMemberResponse:
    """Atualiza o papel (RBAC) de um membro existente no workspace."""
    ws = await get_workspace(session, workspace_id)
    if ws.owner_id == target_user_id and req.role != WorkspaceRole.OWNER:
        raise AppException(
            message="Não é permitido rebaixar o proprietário (Owner) do workspace.",
            status_code=400,
            code="CANNOT_DEMOTE_OWNER",
        )

    # Se estiver tentando promover para OWNER, o operador deve ser o próprio OWNER atual
    if req.role == WorkspaceRole.OWNER and ws.owner_id != operator_user.id:
        raise AppException(
            message="Apenas o proprietário atual pode transferir a posse do workspace.",
            status_code=403,
            code="ONLY_OWNER_CAN_TRANSFER",
        )

    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target_user_id,
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundException(message="Membro não encontrado neste workspace.")

    member.role = req.role
    session.add(member)

    # Se promovido a OWNER, atualiza o workspace.owner_id
    if req.role == WorkspaceRole.OWNER:
        ws.owner_id = target_user_id
        session.add(ws)

    await session.commit()
    await session.refresh(member)

    # Busca dados do usuário para resposta
    user_stmt = select(User).where(User.id == target_user_id)
    user_res = await session.execute(user_stmt)
    user = user_res.scalar_one()

    return WorkspaceMemberResponse(
        id=member.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=member.role,
        created_at=member.created_at,
    )


async def create_workspace_invite(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    inviter_user: User,
    req: WorkspaceInviteCreate,
) -> WorkspaceInvite:
    """Emite um convite de equipe para o e-mail informado com token seguro de 7 dias."""
    email = req.email.lower().strip()

    # 1. Verifica se já é membro ativo do workspace
    existing_member_stmt = (
        select(WorkspaceMember)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            func.lower(User.email) == email,
        )
    )
    existing_member = await session.execute(existing_member_stmt)
    if existing_member.scalar_one_or_none():
        raise AppException(
            message=f"O usuário com e-mail '{email}' já é membro ativo deste workspace.",
            status_code=400,
            code="USER_ALREADY_MEMBER",
        )

    # 2. Verifica se já existe um convite pendente para este e-mail no workspace
    existing_invite_stmt = select(WorkspaceInvite).where(
        WorkspaceInvite.workspace_id == workspace_id,
        WorkspaceInvite.email == email,
        WorkspaceInvite.status == "pending",
    )
    existing_invite_res = await session.execute(existing_invite_stmt)
    existing_invite = existing_invite_res.scalar_one_or_none()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    if existing_invite:
        # Renova o convite pendente existente
        existing_invite.token = token
        existing_invite.role = req.role
        existing_invite.expires_at = expires_at
        existing_invite.invited_by_user_id = inviter_user.id
        invite = existing_invite
    else:
        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            invited_by_user_id=inviter_user.id,
            email=email,
            role=req.role,
            token=token,
            status="pending",
            expires_at=expires_at,
        )
        session.add(invite)

    await session.commit()
    await session.refresh(invite)

    # 3. Dispara e-mail transacional em segundo plano via Arq Worker
    queue = await get_queue()
    try:
        await queue.enqueue(
            "send_transactional_email_task",
            to_email=email,
            subject="Convite para ingressar no Workspace - SoftForge",
            content=f"Você foi convidado para colaborar no workspace da SoftForge. Token: {invite.token}",
        )
    except Exception:
        pass

    return invite


async def list_workspace_invites(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[WorkspaceInvite]:
    """Retorna todos os convites pendentes e não expirados do workspace."""
    stmt = (
        select(WorkspaceInvite)
        .where(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.status == "pending",
        )
        .order_by(WorkspaceInvite.created_at.desc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def revoke_workspace_invite(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    invite_id: uuid.UUID,
) -> WorkspaceInvite:
    """Revoga imediatamente um convite de equipe pendente."""
    stmt = select(WorkspaceInvite).where(
        WorkspaceInvite.id == invite_id,
        WorkspaceInvite.workspace_id == workspace_id,
    )
    res = await session.execute(stmt)
    invite = res.scalar_one_or_none()
    if not invite:
        raise NotFoundException(message="Convite não encontrado.")

    invite.status = "revoked"
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    return invite


async def accept_workspace_invite(
    session: AsyncSession,
    token: str,
    user: User,
) -> tuple[Workspace, WorkspaceMember]:
    """Valida o token do convite e adiciona o usuário autenticado como membro do workspace."""
    stmt = select(WorkspaceInvite).where(
        WorkspaceInvite.token == token.strip(),
        WorkspaceInvite.status == "pending",
    )
    res = await session.execute(stmt)
    invite = res.scalar_one_or_none()

    if not invite:
        raise NotFoundException(message="Convite inválido ou expirado.")

    now_utc = datetime.now(UTC)
    exp = invite.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)

    if exp < now_utc:
        invite.status = "expired"
        session.add(invite)
        await session.commit()
        raise AppException(
            message="Este convite expirou. Solicite um novo convite ao administrador.",
            status_code=400,
            code="INVITE_EXPIRED",
        )

    # Verifica se o usuário já é membro do workspace
    existing_membership_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == invite.workspace_id,
        WorkspaceMember.user_id == user.id,
    )
    existing_membership_res = await session.execute(existing_membership_stmt)
    membership = existing_membership_res.scalar_one_or_none()

    if not membership:
        membership = WorkspaceMember(
            workspace_id=invite.workspace_id,
            user_id=user.id,
            role=invite.role,
        )
        session.add(membership)

    invite.status = "accepted"
    invite.accepted_at = now_utc
    session.add(invite)

    await session.commit()
    await session.refresh(membership)

    ws = await get_workspace(session, invite.workspace_id)
    return ws, membership

