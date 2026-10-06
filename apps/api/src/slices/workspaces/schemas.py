import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.slices.workspaces.models import WorkspaceRole


class WorkspaceCreate(BaseModel):
    """Schema para criação de um novo workspace / tenant."""

    name: str = Field(min_length=2, max_length=100, description="Nome da organização ou workspace")
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Identificador único em formato slug (opcional, gerado do nome se omitido)",
    )


class WorkspaceUpdate(BaseModel):
    """Schema para atualização de dados do workspace."""

    name: str | None = Field(default=None, min_length=2, max_length=100)


class WorkspaceResponse(BaseModel):
    """Schema de resposta com dados do workspace e papel do usuário requisitante."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    role: WorkspaceRole | None = None
    created_at: datetime


class AddMemberRequest(BaseModel):
    """Schema para adicionar ou convidar membro para o workspace."""

    email: EmailStr = Field(description="E-mail do usuário a ser adicionado")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.MEMBER, description="Nível de permissão (RBAC)"
    )


class UpdateMemberRoleRequest(BaseModel):
    """Schema para alterar permissão de membro existente."""

    role: WorkspaceRole = Field(description="Novo nível de permissão")


class WorkspaceMemberResponse(BaseModel):
    """Schema de detalhes de um membro do workspace."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: WorkspaceRole
    created_at: datetime
