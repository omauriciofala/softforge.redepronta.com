import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WebhookEndpointCreate(BaseModel):
    """Schema para cadastro de nova URL de webhook no workspace."""

    url: str = Field(..., max_length=500, description="URL pública HTTPS para receber as notificações")
    description: str | None = Field(None, max_length=255, description="Descrição do objetivo da integração")
    events: list[str] = Field(
        default=["*"],
        description="Lista de eventos assinados (ex: ['project.created', 'member.invited'] ou ['*'])",
    )


class WebhookEndpointUpdate(BaseModel):
    """Schema para atualização parcial de webhook existente."""

    url: str | None = Field(None, max_length=500, description="Nova URL receptora")
    description: str | None = Field(None, max_length=255, description="Descrição atualizada")
    events: list[str] | None = Field(None, description="Nova lista de eventos assinados")
    is_active: bool | None = Field(None, description="Status de ativação do webhook")


class WebhookEndpointResponse(BaseModel):
    """Representação pública de um endpoint de webhook cadastrado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID único do webhook")
    workspace_id: uuid.UUID = Field(..., description="ID do workspace proprietário")
    url: str = Field(..., description="URL receptora dos eventos")
    description: str | None = Field(None, description="Descrição da integração")
    secret: str = Field(..., description="Segredo de assinatura HMAC SHA256")
    events: list[str] = Field(..., description="Eventos aos quais o endpoint está inscrito")
    is_active: bool = Field(..., description="Se o webhook está ativo para disparos")
    created_at: datetime = Field(..., description="Data de criação em UTC")
    updated_at: datetime = Field(..., description="Data de última atualização em UTC")


class WebhookDeliveryResponse(BaseModel):
    """Detalhes de uma tentativa de entrega de evento de webhook."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID único da entrega")
    endpoint_id: uuid.UUID = Field(..., description="ID do endpoint receptor")
    event_type: str = Field(..., description="Tipo do evento disparado (ex: project.created)")
    payload: dict[str, Any] = Field(..., description="Carga JSON enviada")
    response_status_code: int | None = Field(None, description="Status code HTTP retornado pelo receptor")
    response_body: str | None = Field(None, description="Primeiros caracteres do corpo da resposta")
    attempt: int = Field(..., description="Número da tentativa de entrega")
    status: str = Field(..., description="Status da entrega ('pending', 'success', 'failed')")
    error_message: str | None = Field(None, description="Mensagem de erro de conexão ou timeout, se houver")
    delivered_at: datetime | None = Field(None, description="Data e hora da confirmação de entrega")
    created_at: datetime = Field(..., description="Data e hora da tentativa inicial")


class WebhookDeliveryListResponse(BaseModel):
    """Lista paginada de histórico de entregas de webhooks."""

    items: list[WebhookDeliveryResponse] = Field(..., description="Lista de tentativas de entrega")
    total: int = Field(..., description="Total de entregas registradas")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Itens por página")
