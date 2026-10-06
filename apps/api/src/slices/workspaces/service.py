import re
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, NotFoundException
from src.slices.auth.models import User
from src.slices.auth.service import get_user_by_email
from src.slices.workspaces.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from src.slices.workspaces.schemas import (
    AddMemberRequest,
    WorkspaceCreate,
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
