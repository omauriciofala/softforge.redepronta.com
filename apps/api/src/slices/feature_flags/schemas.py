import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeatureFlagBase(BaseModel):
    key: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9_-]+$",
        description="Identificador único em formato slug (letras minúsculas, números, hífens ou underscores)",
        examples=["ai_copilot", "export_pdf", "beta_dashboard"],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nome amigável da funcionalidade",
        examples=["Assistente de IA Integrado"],
    )
    description: str | None = Field(
        None,
        max_length=255,
        description="Descrição do comportamento da feature flag",
        examples=["Habilita o assistente interativo de IA no painel do usuário"],
    )
    is_enabled: bool = Field(
        default=False,
        description="Estado padrão global da flag",
    )


class FeatureFlagCreate(FeatureFlagBase):
    pass


class FeatureFlagUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=255)
    is_enabled: bool | None = None


class FeatureFlagRead(FeatureFlagBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FeatureFlagOverrideSet(BaseModel):
    is_enabled: bool = Field(
        ...,
        description="Status da flag para o workspace específico (sobrescreve o padrão global)",
    )


class FeatureFlagOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    feature_flag_id: uuid.UUID
    workspace_id: uuid.UUID
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceFlagsEvaluation(BaseModel):
    workspace_id: uuid.UUID
    flags: dict[str, bool] = Field(
        ...,
        description="Dicionário de flags avaliadas contendo a chave e o status booleano resultante",
        examples=[{"ai_copilot": True, "export_pdf": False}],
    )
    evaluated_at: datetime
