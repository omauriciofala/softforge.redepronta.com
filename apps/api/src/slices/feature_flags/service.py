import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppException, NotFoundException
from src.slices.feature_flags.models import FeatureFlag, FeatureFlagOverride
from src.slices.feature_flags.schemas import FeatureFlagCreate, FeatureFlagUpdate


class FeatureFlagService:
    @staticmethod
    async def list_flags(db: AsyncSession) -> Sequence[FeatureFlag]:
        result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.name.asc()))
        return result.scalars().all()

    @staticmethod
    async def get_flag_by_id(db: AsyncSession, flag_id: uuid.UUID) -> FeatureFlag | None:
        result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_flag_by_key(db: AsyncSession, key: str) -> FeatureFlag | None:
        result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_flag(db: AsyncSession, data: FeatureFlagCreate) -> FeatureFlag:
        existing = await FeatureFlagService.get_flag_by_key(db, data.key)
        if existing:
            raise AppException(
                message=f"Já existe uma feature flag cadastrada com a chave '{data.key}'",
                status_code=409,
                code="FEATURE_FLAG_KEY_EXISTS",
            )

        flag = FeatureFlag(
            key=data.key.strip().lower(),
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            is_enabled=data.is_enabled,
        )
        db.add(flag)
        await db.commit()
        await db.refresh(flag)
        return flag

    @staticmethod
    async def update_flag(
        db: AsyncSession,
        flag: FeatureFlag,
        data: FeatureFlagUpdate,
    ) -> FeatureFlag:
        if data.name is not None:
            flag.name = data.name.strip()
        if data.description is not None:
            flag.description = data.description.strip() if data.description else None
        if data.is_enabled is not None:
            flag.is_enabled = data.is_enabled

        await db.commit()
        await db.refresh(flag)
        return flag

    @staticmethod
    async def delete_flag(db: AsyncSession, flag: FeatureFlag) -> None:
        await db.delete(flag)
        await db.commit()

    @staticmethod
    async def get_workspace_override(
        db: AsyncSession,
        flag_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> FeatureFlagOverride | None:
        result = await db.execute(
            select(FeatureFlagOverride).where(
                FeatureFlagOverride.feature_flag_id == flag_id,
                FeatureFlagOverride.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set_workspace_override(
        db: AsyncSession,
        flag_id: uuid.UUID,
        workspace_id: uuid.UUID,
        is_enabled: bool,
    ) -> FeatureFlagOverride:
        flag = await FeatureFlagService.get_flag_by_id(db, flag_id)
        if not flag:
            raise NotFoundException(f"Feature flag com ID '{flag_id}' não encontrada")

        override = await FeatureFlagService.get_workspace_override(db, flag_id, workspace_id)
        if override:
            override.is_enabled = is_enabled
        else:
            override = FeatureFlagOverride(
                feature_flag_id=flag_id,
                workspace_id=workspace_id,
                is_enabled=is_enabled,
            )
            db.add(override)

        await db.commit()
        await db.refresh(override)
        return override

    @staticmethod
    async def remove_workspace_override(
        db: AsyncSession,
        flag_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> bool:
        result = await db.execute(
            delete(FeatureFlagOverride).where(
                FeatureFlagOverride.feature_flag_id == flag_id,
                FeatureFlagOverride.workspace_id == workspace_id,
            )
        )
        await db.commit()
        return (result.rowcount or 0) > 0

    @staticmethod
    async def evaluate_flag_for_workspace(
        db: AsyncSession,
        key: str,
        workspace_id: uuid.UUID | None,
    ) -> bool:
        flag = await FeatureFlagService.get_flag_by_key(db, key)
        if not flag:
            return False

        if workspace_id:
            override = await FeatureFlagService.get_workspace_override(db, flag.id, workspace_id)
            if override is not None:
                return override.is_enabled

        return flag.is_enabled

    @staticmethod
    async def evaluate_all_flags_for_workspace(
        db: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> dict[str, bool]:
        all_flags = await FeatureFlagService.list_flags(db)
        if not all_flags:
            return {}

        result = await db.execute(
            select(FeatureFlagOverride).where(FeatureFlagOverride.workspace_id == workspace_id)
        )
        overrides = {ov.feature_flag_id: ov.is_enabled for ov in result.scalars().all()}

        return {
            flag.key: overrides.get(flag.id, flag.is_enabled)
            for flag in all_flags
        }
