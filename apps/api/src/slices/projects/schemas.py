import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TaskStatus = Literal["todo", "in_progress", "done"]
TaskPriority = Literal["low", "medium", "high"]


class ProjectCreate(BaseModel):
    """Schema para criação de um novo projeto."""

    name: str = Field(min_length=2, max_length=100, description="Nome do projeto")
    description: str | None = Field(
        default=None, max_length=1000, description="Descrição detalhada"
    )


class ProjectUpdate(BaseModel):
    """Schema para atualização parcial do projeto."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_archived: bool | None = None


class ProjectResponse(BaseModel):
    """Schema com informações do projeto e contagem de tarefas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
    tasks_count: int = 0


class PaginatedProjectsResponse(BaseModel):
    """Schema de lista paginada de projetos."""

    items: list[ProjectResponse]
    total: int
    limit: int
    offset: int


class TaskCreate(BaseModel):
    """Schema para criação de uma tarefa dentro de um projeto."""

    title: str = Field(min_length=2, max_length=200, description="Título da tarefa")
    status: TaskStatus = Field(default="todo")
    priority: TaskPriority = Field(default="medium")
    due_date: datetime | None = None
    assigned_to_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    """Schema para atualização de dados ou status de uma tarefa."""

    title: str | None = Field(default=None, min_length=2, max_length=200)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assigned_to_id: uuid.UUID | None = None


class TaskResponse(BaseModel):
    """Schema de resposta com dados completos da tarefa."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    status: str
    priority: str
    due_date: datetime | None
    assigned_to_id: uuid.UUID | None
    created_at: datetime
