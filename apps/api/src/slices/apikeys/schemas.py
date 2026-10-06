import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """Schema de requisição para criação de uma nova chave de API."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nome identificador da chave (ex: 'Cursor AI Agent', 'GitHub Actions CI')",
        examples=["Cursor AI Agent"],
    )
    scopes: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Lista de escopos concedidos à chave (ex: ['*'], ['projects:read'])",
        examples=[["*"]],
    )
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Duração da validade da chave em dias. Se omitido, a chave não expira automaticamente.",
        examples=[30],
    )


class ApiKeyResponse(BaseModel):
    """Schema público de retorno de uma chave de API (nunca expõe o segredo completo)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    key_prefix: str = Field(
        description="Prefixo público mascarado para identificação (ex: 'sf_live_abc1...9xyz')"
    )
    scopes: list[str]
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_revoked: bool
    revoked_at: datetime | None = None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Schema retornado exclusivamente na criação da chave, contendo o segredo em texto puro."""

    raw_key: str = Field(
        description="Chave de API secreta completa. Guarde com segurança, pois ela NUNCA será exibida novamente!"
    )


class ApiKeyListResponse(BaseModel):
    """Schema de listagem paginada/consolidada de chaves de API do workspace."""

    items: list[ApiKeyResponse]
    total: int
