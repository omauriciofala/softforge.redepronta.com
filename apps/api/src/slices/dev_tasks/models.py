import enum
import uuid

from sqlalchemy import JSON, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class DevTaskStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class DevTaskType(enum.StrEnum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOC = "doc"
    CHORE = "chore"


class DevTaskPriority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DevTaskNoteType(enum.StrEnum):
    PROGRESS = "progress"
    DECISION = "decision"
    BLOCKER = "blocker"
    VERIFICATION = "verification"


class DevTask(Base):
    __tablename__ = "dev_tasks"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), default=DevTaskType.FEATURE.value, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default=DevTaskPriority.MEDIUM.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=DevTaskStatus.TODO.value, index=True, nullable=False)

    target_files: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verification_command: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    git_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    notes: Mapped[list["DevTaskNote"]] = relationship(
        "DevTaskNote",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DevTaskNote.created_at.asc()",
    )


class DevTaskNote(Base):
    __tablename__ = "dev_task_notes"

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dev_tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), default=DevTaskNoteType.PROGRESS.value, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    task: Mapped["DevTask"] = relationship("DevTask", back_populates="notes")
