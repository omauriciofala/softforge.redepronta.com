import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import NotFoundException
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.themes.schemas import (
    ThemeManifest,
    WorkspaceThemeRead,
    WorkspaceThemeUpdate,
)
from src.slices.themes.service import ThemeService
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(tags=["Temas & White-labeling"])


# ============================================================================
# ENDPOINTS GLOBAIS DE SISTEMA (/system/themes)
# ============================================================================


@router.get(
    "/system/themes",
    response_model=list[ThemeManifest],
    summary="Listar temas disponíveis no sistema",
    description="Retorna a lista de manifestos de todos os temas e engines de frontend instalados no diretório themes/.",
)
async def list_system_themes() -> list[ThemeManifest]:
    return ThemeService.discover_installed_themes()


@router.get(
    "/system/themes/{slug}",
    response_model=ThemeManifest,
    summary="Obter detalhes e manifesto de um tema específico",
    description="Retorna o manifesto declarativo e design tokens completos do tema identificado pelo slug.",
)
async def get_system_theme(
    slug: Annotated[str, Path(description="Identificador único (slug) do tema")],
) -> ThemeManifest:
    theme = ThemeService.get_theme_by_slug(slug)
    if not theme:
        raise NotFoundException(
            message=f"Tema com slug '{slug}' não encontrado",
            message_key="errors.theme_not_found",
            message_kwargs={"slug": slug},
        )
    return theme


# ============================================================================
# ENDPOINTS DE WORKSPACE / TENANT (/workspaces/{workspace_id}/theme)
# ============================================================================


@router.get(
    "/workspaces/{workspace_id}/theme",
    response_model=WorkspaceThemeRead,
    summary="Obter tema e branding consolidados do workspace",
    description="Retorna as variáveis CSS (--sf-*), logo customizada e tokens consolidados para o workspace (requer cargo mínimo Viewer).",
)
async def get_workspace_theme(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceThemeRead:
    _ = membership
    return await ThemeService.evaluate_workspace_theme(session, workspace_id)


@router.patch(
    "/workspaces/{workspace_id}/theme",
    response_model=WorkspaceThemeRead,
    summary="Atualizar tema e customizações de marca do workspace",
    description="Altera o tema ativo, logo, cor primária, CSS customizado ou tokens granulares do tenant (requer cargo mínimo Admin).",
)
async def update_workspace_theme(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
    data: WorkspaceThemeUpdate,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> WorkspaceThemeRead:
    _ = membership
    updated_theme = await ThemeService.update_workspace_theme(session, workspace_id, data)

    await log_audit_event(
        action="theme.updated",
        resource_type="workspace_theme",
        resource_id=str(workspace_id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    return updated_theme
