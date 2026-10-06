import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.slices.workspaces.models import Workspace


class FeatureFlag(Base):
    """Definição global de Feature Flag no sistema."""

    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    overrides: Mapped[list["FeatureFlagOverride"]] = relationship(
        "FeatureFlagOverride",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FeatureFlagOverride(Base):
    """Substituição de valor de Feature Flag específico por Workspace (Tenant)."""

    __tablename__ = "feature_flag_overrides"
    __table_args__ = (
        UniqueConstraint("feature_flag_id", "workspace_id", name="uq_feature_flag_workspace_override"),
    )

    feature_flag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    feature_flag: Mapped["FeatureFlag"] = relationship("FeatureFlag", back_populates="overrides")
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
