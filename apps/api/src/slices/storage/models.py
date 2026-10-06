import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.slices.auth.models import User
    from src.slices.workspaces.models import Workspace


class StoredFile(Base):
    """Metadados de arquivo persistido no sistema de armazenamento (Local / S3 / MinIO)."""

    __tablename__ = "stored_files"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    user: Mapped["User"] = relationship("User", lazy="joined")
    workspace: Mapped["Workspace | None"] = relationship("Workspace", lazy="selectin")
