import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.slices.dev_tasks.models import (
    DevTaskNoteType,
    DevTaskPriority,
    DevTaskStatus,
    DevTaskType,
)


class DevTaskNoteCreate(BaseModel):
    author: str = Field(min_length=1, max_length=100, description="Autor da nota (ex: agente ou humano)")
    note_type: DevTaskNoteType = Field(default=DevTaskNoteType.PROGRESS, description="Tipo da anotação")
    content: str = Field(min_length=1, description="Conteúdo textual da anotação")


class DevTaskNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    author: str
    note_type: str
    content: str
    created_at: datetime


class DevTaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200, description="Título conciso da tarefa de desenvolvimento")
    description: str | None = Field(default=None, description="Objetivo detalhado, contexto e instruções para o agente")
    project_id: uuid.UUID | None = Field(default=None, description="ID do projeto vinculado (opcional)")
    task_type: DevTaskType = Field(default=DevTaskType.FEATURE, description="Tipo da tarefa")
    priority: DevTaskPriority = Field(default=DevTaskPriority.MEDIUM, description="Nível de prioridade")
    target_files: list[str] = Field(default_factory=list, description="Lista de caminhos de arquivos impactados")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Checklist de critérios de aceite")
    verification_command: str | None = Field(default=None, max_length=500, description="Comando técnico a executar para verificar conclusão")
    git_branch: str | None = Field(default=None, max_length=100, description="Branch git de trabalho")
    assigned_agent: str | None = Field(default=None, max_length=100, description="Identificador do agente de IA alocado")


class DevTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    project_id: uuid.UUID | None = None
    task_type: DevTaskType | None = None
    priority: DevTaskPriority | None = None
    status: DevTaskStatus | None = None
    target_files: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    verification_command: str | None = Field(default=None, max_length=500)
    git_branch: str | None = Field(default=None, max_length=100)
    assigned_agent: str | None = Field(default=None, max_length=100)


class DevTaskClaim(BaseModel):
    agent_name: str = Field(min_length=2, max_length=100, description="Nome ou identificador do agente que assume a tarefa")


class DevTaskComplete(BaseModel):
    summary: str = Field(min_length=2, description="Resumo técnico das mudanças realizadas e verificação")
    execute_verification: bool = Field(default=True, description="Se True, executa o comando de verificação e exige código 0")


class DevTaskFail(BaseModel):
    reason: str = Field(min_length=2, description="Motivo do impedimento ou da falha técnica")
    is_blocked: bool = Field(default=False, description="Se True, marca como 'blocked'; se False, marca como 'failed'")
    blocker_details: str | None = Field(default=None, description="Detalhes adicionais do bloqueio ou trace de erro")


class DevTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    description: str | None
    task_type: str
    priority: str
    status: str
    target_files: list[str]
    acceptance_criteria: list[str]
    verification_command: str | None
    verification_output: str | None
    git_branch: str | None
    assigned_agent: str | None
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    notes: list[DevTaskNoteResponse] = []


class DevTaskListResponse(BaseModel):
    items: list[DevTaskResponse]
    total: int
