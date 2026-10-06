import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import ForbiddenException
from src.slices.billing.models import BillingTargetType, PlanTier
from src.slices.billing.service import get_or_create_subscription


def check_quota(resource: str) -> Callable[..., None]:
    """Dependência declarativa do FastAPI que valida quotas antes de permitir criação de recursos.

    Uso:
        @router.post("/projects", dependencies=[Depends(check_quota("projects"))])
    """

    async def _quota_checker(
        workspace_id: uuid.UUID,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> None:
        subscription = await get_or_create_subscription(
            session=session,
            user_id=uuid.uuid4(),  # Fallback caso seja por workspace
            workspace_id=workspace_id,
            target_type=BillingTargetType.WORKSPACE,
        )

        if resource == "projects":
            if subscription.max_projects == -1:
                return  # Ilimitado

            from src.slices.projects.models import Project

            stmt = select(func.count(Project.id)).where(
                Project.workspace_id == workspace_id,
                Project.is_archived.is_(False),
            )
            count = (await session.execute(stmt)).scalar() or 0

            if count >= subscription.max_projects:
                raise ForbiddenException(
                    f"Limite de projetos atingido ({count}/{subscription.max_projects}). "
                    f"Faça upgrade para o Plano Pro em /billing para criar mais projetos."
                )

        elif resource == "members":
            if subscription.max_members == -1:
                return  # Ilimitado

            from src.slices.workspaces.models import WorkspaceMember

            stmt = select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace_id,
            )
            count = (await session.execute(stmt)).scalar() or 0

            if count >= subscription.max_members:
                raise ForbiddenException(
                    f"Limite de membros da equipe atingido ({count}/{subscription.max_members}). "
                    f"Faça upgrade de plano para adicionar mais colaboradores."
                )

    return _quota_checker


def require_plan_tier(min_tier: PlanTier) -> Callable[..., None]:
    """Dependência declarativa que exige um plano mínimo para acessar rotas restritas."""

    async def _plan_checker(
        workspace_id: uuid.UUID,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> None:
        subscription = await get_or_create_subscription(
            session=session,
            user_id=uuid.uuid4(),
            workspace_id=workspace_id,
            target_type=BillingTargetType.WORKSPACE,
        )

        tier_weights = {PlanTier.FREE: 1, PlanTier.PRO: 2, PlanTier.ENTERPRISE: 3}
        current_weight = tier_weights.get(PlanTier(subscription.plan_tier), 1)
        required_weight = tier_weights.get(min_tier, 1)

        if current_weight < required_weight:
            raise ForbiddenException(
                f"Recurso restrito a assinantes do plano {min_tier.value.upper()}. "
                f"Plano atual: {subscription.plan_tier.upper()}."
            )

    return _plan_checker
