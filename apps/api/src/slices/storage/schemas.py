import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoredFileResponse(BaseModel):
    """Schema de metadados e URL de download de um arquivo armazenado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    uploaded_by_user_id: uuid.UUID
    filename: str
    content_type: str
    file_size_bytes: int
    storage_backend: str
    is_public: bool
    download_url: str = Field(description="URL para download ou streaming do arquivo")
    created_at: datetime


class StoredFileListResponse(BaseModel):
    """Schema de listagem de arquivos armazenados."""

    items: list[StoredFileResponse]
    total: int


class AvatarUploadResponse(BaseModel):
    """Schema de resposta após upload de foto de perfil / avatar."""

    avatar_url: str = Field(description="URL pública do avatar atualizado")
    file_id: uuid.UUID = Field(description="ID do registro em stored_files")
