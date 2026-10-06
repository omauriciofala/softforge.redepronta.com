import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Representação de uma notificação in-app."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único da notificação")
    user_id: uuid.UUID = Field(..., description="ID do usuário destinatário")
    workspace_id: uuid.UUID | None = Field(None, description="Workspace associado à notificação, se aplicável")
    title: str = Field(..., description="Título da notificação")
    message: str = Field(..., description="Mensagem ou descrição detalhada")
    category: str = Field("general", description="Categoria (ex: billing, project, system, security)")
    action_url: str | None = Field(None, description="URL de navegação ao clicar na notificação")
    is_read: bool = Field(False, description="Indica se a notificação já foi lida")
    read_at: datetime | None = Field(None, description="Data e hora em que a notificação foi marcada como lida")
    created_at: datetime = Field(..., description="Data e hora de emissão em UTC")


class NotificationListResponse(BaseModel):
    """Lista paginada de notificações in-app com contador de não lidas."""

    items: list[NotificationResponse] = Field(..., description="Lista de notificações do usuário")
    total: int = Field(..., description="Total de notificações do usuário")
    unread_count: int = Field(..., description="Total de notificações pendentes de leitura")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Itens por página")


class UnreadCountResponse(BaseModel):
    """Contador simples de notificações não lidas para o badge do sino na UI."""

    unread_count: int = Field(..., description="Quantidade de notificações não lidas")


class MarkAllReadResponse(BaseModel):
    """Resposta após marcar todas as notificações como lidas."""

    marked_count: int = Field(..., description="Quantidade de notificações atualizadas para lidas")
