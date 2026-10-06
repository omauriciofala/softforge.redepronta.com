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
    avatar_url: str | None = None
    role: WorkspaceRole
    created_at: datetime


class WorkspaceMemberListResponse(BaseModel):
    """Schema para listagem de membros do workspace."""

    items: list[WorkspaceMemberResponse]
    total: int


class WorkspaceInviteCreate(BaseModel):
    """Schema para emissão de um novo convite de equipe."""

    email: EmailStr = Field(description="E-mail corporativo da pessoa convidada")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.MEMBER,
        description="Cargo RBAC atribuído ao membro quando o convite for aceito",
    )


class WorkspaceInviteResponse(BaseModel):
    """Schema de dados do convite de equipe."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    invited_by_user_id: uuid.UUID
    email: str
    role: WorkspaceRole
    status: str
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime


class WorkspaceInviteListResponse(BaseModel):
    """Schema de listagem de convites do workspace."""

    items: list[WorkspaceInviteResponse]
    total: int


class WorkspaceInviteAcceptRequest(BaseModel):
    """Schema para aceitar um convite de equipe via token."""

    token: str = Field(min_length=10, description="Token criptográfico do convite recebido")

