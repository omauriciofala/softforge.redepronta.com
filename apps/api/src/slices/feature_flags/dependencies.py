import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import FeatureFlagDisabledException
from src.slices.feature_flags.service import FeatureFlagService


def require_feature_flag(flag_key: str) -> Callable[..., object]:
    """
    Fábrica de dependências FastAPI para proteger endpoints com Feature Flags.
    Avalia o estado global ou o override específico do workspace (se houver 'workspace_id'
    na rota ou nos parâmetros de busca). Caso desabilitada, lança HTTP 403 Forbidden.
    """

    async def _checker(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> bool:
        workspace_id: uuid.UUID | None = None
        raw_ws = request.path_params.get("workspace_id") or request.query_params.get("workspace_id")
        if raw_ws:
            try:
                workspace_id = uuid.UUID(str(raw_ws))
            except ValueError:
                pass

        enabled = await FeatureFlagService.evaluate_flag_for_workspace(
            db=session,
            key=flag_key,
            workspace_id=workspace_id,
        )
        if not enabled:
            raise FeatureFlagDisabledException(flag_key=flag_key)

        return True

    return _checker
