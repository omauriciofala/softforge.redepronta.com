import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import NotFoundException
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.feature_flags.dependencies import require_feature_flag
from src.slices.feature_flags.models import FeatureFlag
from src.slices.feature_flags.schemas import (
    FeatureFlagCreate,
    FeatureFlagOverrideRead,
    FeatureFlagOverrideSet,
    FeatureFlagRead,
    FeatureFlagUpdate,
    WorkspaceFlagsEvaluation,
)
from src.slices.feature_flags.service import FeatureFlagService
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(tags=["Feature Flags & Toggles"])


# ============================================================================
# ENDPOINTS GLOBAIS DE SISTEMA (/system/features)
# ============================================================================


@router.get(
    "/system/features",
    response_model=list[FeatureFlagRead],
    summary="Listar todas as feature flags do sistema",
    description="Retorna a lista completa de feature flags cadastradas e seus estados padrão globais.",
)
async def list_features(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[FeatureFlag]:
    _ = current_user
    flags = await FeatureFlagService.list_flags(session)
    return list(flags)


@router.post(
    "/system/features",
    response_model=FeatureFlagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova feature flag global",
    description="Cria uma nova flag no catálogo do sistema com status padrão ativo ou inativo.",
)
async def create_feature(
    data: FeatureFlagCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> FeatureFlag:
    flag = await FeatureFlagService.create_flag(session, data)

    await log_audit_event(
        action="feature_flag.created",
        resource_type="feature_flag",
        resource_id=str(flag.id),
        workspace_id=None,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    return flag


@router.get(
    "/system/features/{flag_id}",
    response_model=FeatureFlagRead,
    summary="Obter detalhes de uma feature flag por ID",
)
async def get_feature(
    flag_id: Annotated[uuid.UUID, Path(description="ID da Feature Flag")],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FeatureFlag:
    _ = current_user
    flag = await FeatureFlagService.get_flag_by_id(session, flag_id)
    if not flag:
        raise NotFoundException(
            message=f"Feature flag com ID '{flag_id}' não encontrada",
            message_key="errors.feature_flag_not_found",
            message_kwargs={"flag_id": str(flag_id)},
        )
    return flag


@router.patch(
    "/system/features/{flag_id}",
    response_model=FeatureFlagRead,
    summary="Atualizar parâmetros ou estado global da feature flag",
)
async def update_feature(
    flag_id: Annotated[uuid.UUID, Path(description="ID da Feature Flag")],
    data: FeatureFlagUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> FeatureFlag:
    flag = await FeatureFlagService.get_flag_by_id(session, flag_id)
    if not flag:
        raise NotFoundException(
            message=f"Feature flag com ID '{flag_id}' não encontrada",
            message_key="errors.feature_flag_not_found",
            message_kwargs={"flag_id": str(flag_id)},
        )

    updated = await FeatureFlagService.update_flag(session, flag, data)

    await log_audit_event(
        action="feature_flag.updated",
        resource_type="feature_flag",
        resource_id=str(flag.id),
        workspace_id=None,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    return updated


@router.delete(
    "/system/features/{flag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir feature flag do sistema",
)
async def delete_feature(
    flag_id: Annotated[uuid.UUID, Path(description="ID da Feature Flag")],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> None:
    flag = await FeatureFlagService.get_flag_by_id(session, flag_id)
    if not flag:
        raise NotFoundException(
            message=f"Feature flag com ID '{flag_id}' não encontrada",
            message_key="errors.feature_flag_not_found",
            message_kwargs={"flag_id": str(flag_id)},
        )

    await FeatureFlagService.delete_flag(session, flag)

    await log_audit_event(
        action="feature_flag.deleted",
        resource_type="feature_flag",
        resource_id=str(flag_id),
        workspace_id=None,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )


# ============================================================================
# ENDPOINTS ESPECÍFICOS DE WORKSPACE / TENANT (/workspaces/{workspace_id}/features)
# ============================================================================


@router.get(
    "/workspaces/{workspace_id}/features",
    response_model=WorkspaceFlagsEvaluation,
    summary="Avaliar todas as feature flags para o workspace atual",
    description="Retorna o mapa completo de flags consolidadas com base no estado global e nos overrides aplicados ao tenant.",
)
async def evaluate_workspace_features(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceFlagsEvaluation:
    _ = membership
    evaluated = await FeatureFlagService.evaluate_all_flags_for_workspace(session, workspace_id)
    return WorkspaceFlagsEvaluation(
        workspace_id=workspace_id,
        flags=evaluated,
        evaluated_at=datetime.now(UTC),
    )


@router.post(
    "/workspaces/{workspace_id}/features/{flag_id}/override",
    response_model=FeatureFlagOverrideRead,
    summary="Definir substituição (override) de feature flag para o workspace",
    description="Força a ativação ou desativação de uma flag exclusivamente para este workspace (requer cargo mínimo Admin).",
)
async def set_workspace_flag_override(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
    flag_id: Annotated[uuid.UUID, Path(description="ID da Feature Flag")],
    data: FeatureFlagOverrideSet,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> FeatureFlagOverrideRead:
    _ = membership
    override = await FeatureFlagService.set_workspace_override(
        session, flag_id, workspace_id, data.is_enabled
    )

    await log_audit_event(
        action="feature_flag.override_set",
        resource_type="feature_flag_override",
        resource_id=str(override.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )
    return FeatureFlagOverrideRead.model_validate(override)


@router.delete(
    "/workspaces/{workspace_id}/features/{flag_id}/override",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover substituição de feature flag do workspace",
    description="Remove o override do workspace, restaurando o comportamento herdado do estado global da flag.",
)
async def remove_workspace_flag_override(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
    flag_id: Annotated[uuid.UUID, Path(description="ID da Feature Flag")],
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> None:
    _ = membership
    removed = await FeatureFlagService.remove_workspace_override(session, flag_id, workspace_id)
    if not removed:
        raise NotFoundException("Nenhum override encontrado para esta flag neste workspace")

    await log_audit_event(
        action="feature_flag.override_removed",
        resource_type="feature_flag_override",
        resource_id=str(flag_id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )


@router.get(
    "/workspaces/{workspace_id}/features/demo-guarded",
    summary="Endpoint de demonstração protegido por Feature Flag",
    description="Endpoint modelo protegido pela dependência require_feature_flag('beta_copilot').",
    dependencies=[
        Depends(require_workspace_role(WorkspaceRole.VIEWER)),
        Depends(require_feature_flag("beta_copilot")),
    ],
)
async def demo_guarded_endpoint(
    workspace_id: Annotated[uuid.UUID, Path(description="ID do Workspace")],
) -> dict[str, str]:
    return {
        "status": "allowed",
        "feature": "beta_copilot",
        "workspace_id": str(workspace_id),
        "message": "Acesso concedido pela Feature Flag 'beta_copilot'!",
    }
