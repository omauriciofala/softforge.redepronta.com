import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.slices.workspaces.models import Workspace


class WorkspaceTheme(Base):
    """Configurações visuais, motor de frontend e personalizações de marca (White-labeling) por Workspace."""

    __tablename__ = "workspace_themes"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    theme_slug: Mapped[str] = mapped_column(String(100), default="default-react", nullable=False)
    custom_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    custom_primary_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    custom_css: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_override: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
