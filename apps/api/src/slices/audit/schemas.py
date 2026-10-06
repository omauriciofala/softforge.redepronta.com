import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Representação de um registro imutável de auditoria."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único do evento de auditoria")
    workspace_id: uuid.UUID | None = Field(None, description="Workspace associado à ação, se aplicável")
    user_id: uuid.UUID | None = Field(None, description="Usuário que executou a ação")
    user_email: str | None = Field(None, description="E-mail do autor no momento da ação")
    action: str = Field(..., description="Nome da ação realizada (ex: auth.login, project.created)")
    resource_type: str = Field(..., description="Tipo do recurso afetado (ex: project, user, workspace)")
    resource_id: str | None = Field(None, description="ID do recurso afetado")
    ip_address: str | None = Field(None, description="Endereço IP de origem")
    user_agent: str | None = Field(None, description="User-Agent do cliente HTTP")
    created_at: datetime = Field(..., description="Data e hora do registro em UTC")


class AuditLogListResponse(BaseModel):
    """Lista paginada de registros de auditoria."""

    items: list[AuditLogResponse] = Field(..., description="Lista de eventos de auditoria")
    total: int = Field(..., description="Total de eventos correspondentes aos filtros")
    page: int = Field(..., description="Página atual (base 1)")
    page_size: int = Field(..., description="Quantidade de itens por página")
