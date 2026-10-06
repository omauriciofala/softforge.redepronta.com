import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Schema para criação de nova conta de usuário."""

    email: EmailStr = Field(description="Endereço de e-mail corporativo ou pessoal")
    password: str = Field(min_length=8, description="Senha de acesso (mínimo 8 caracteres)")
    full_name: str = Field(min_length=2, max_length=100, description="Nome completo do usuário")


class UserLoginRequest(BaseModel):
    """Schema para autenticação e obtenção de token."""

    email: EmailStr = Field(description="E-mail cadastrado")
    password: str = Field(description="Senha de acesso")


class TokenResponse(BaseModel):
    """Schema com tokens JWT retornados na autenticação."""

    access_token: str = Field(description="JWT de curta duração para autorização de requisições")
    refresh_token: str = Field(description="Token de renovação para estender a sessão")
    token_type: str = Field(default="bearer", description="Tipo de autenticação (Bearer)")


class RefreshTokenRequest(BaseModel):
    """Schema para solicitar renovação do access token."""

    refresh_token: str = Field(description="Token de refresh válido")


class UserResponse(BaseModel):
    """Schema com dados públicos do usuário."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
