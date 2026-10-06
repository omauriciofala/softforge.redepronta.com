import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import ForbiddenException
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.workspaces.models import (
    ROLE_HIERARCHY,
    WorkspaceMember,
    WorkspaceRole,
)


def require_workspace_role(
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
) -> Callable[..., object]:
    """
    Fábrica de dependências que valida se o usuário autenticado é membro do workspace
    e possui permissão igual ou superior ao papel exigido (RBAC).
    """

    async def _checker(
        workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> WorkspaceMember:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise ForbiddenException(message="Você não é membro deste workspace")

        user_level = ROLE_HIERARCHY.get(member.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)

        if user_level < required_level:
            raise ForbiddenException(
                message=f"Esta ação requer papel mínimo '{min_role.value}'. Seu papel atual é '{member.role.value}'."
            )

        return member

    return _checker
