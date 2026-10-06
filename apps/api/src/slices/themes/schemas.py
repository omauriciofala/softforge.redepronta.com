import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ThemeTokens(BaseModel):
    """Estrutura dos design tokens universais contidos no manifesto."""

    model_config = ConfigDict(extra="allow")

    colors: dict[str, str] = Field(default_factory=dict, description="Mapa de cores dos tokens universais")
    typography: dict[str, str] = Field(default_factory=dict, description="Tokens de tipografia e fontes")
    geometry: dict[str, str] = Field(default_factory=dict, description="Tokens de geometria, bordas e espaçamentos")


class ThemeAssets(BaseModel):
    """Folhas de estilo e scripts adicionais necessários para o tema."""

    model_config = ConfigDict(extra="allow")

    stylesheets: list[str] = Field(default_factory=list, description="Lista de folhas de estilo CSS")
    scripts: list[str] = Field(default_factory=list, description="Lista de scripts JS")


class ThemeManifest(BaseModel):
    """Manifesto declarativo universal de um tema (softforge-theme.json)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Nome amigável do tema")
    slug: str = Field(..., description="Identificador único em formato kebab-case")
    version: str = Field(default="1.0.0", description="Versão do tema")
    engine: str = Field(..., description="Motor visual ou framework (ex: react, html-bootstrap, vue, php)")
    author: str | None = Field(default=None, description="Autor ou mantenedor do tema")
    description: str | None = Field(default=None, description="Breve descrição da proposta visual")
    homepage: str | None = Field(default=None, description="URL de documentação do tema")
    preview_image: str | None = Field(default=None, description="Caminho relativo para imagem de prévia")
    tokens: ThemeTokens = Field(default_factory=ThemeTokens, description="Design tokens universais")
    assets: ThemeAssets = Field(default_factory=ThemeAssets, description="Recursos estáticos do tema")


class WorkspaceThemeRead(BaseModel):
    """Configurações visuais consolidadas e tokens avaliados para o workspace."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID = Field(..., description="ID do Workspace associado")
    theme_slug: str = Field(..., description="Slug do tema ativo")
    theme_name: str = Field(..., description="Nome de exibição do tema ativo")
    theme_engine: str = Field(..., description="Motor visual do tema ativo (react, html-bootstrap, etc.)")
    custom_logo_url: str | None = Field(default=None, description="URL de logo customizada do tenant")
    custom_primary_color: str | None = Field(default=None, description="Cor primária customizada do tenant")
    custom_css: str | None = Field(default=None, description="CSS adicional injetado pelo tenant")
    tokens: dict[str, Any] = Field(default_factory=dict, description="Tokens universais consolidados")
    tokens_override: dict[str, Any] = Field(default_factory=dict, description="Substituições específicas de tokens")
    css_variables: dict[str, str] = Field(
        default_factory=dict,
        description="Variáveis CSS prontas para injeção no :root (--sf-*)",
    )


class WorkspaceThemeUpdate(BaseModel):
    """Payload para atualização de tema e marca (White-labeling) do workspace."""

    model_config = ConfigDict(extra="forbid")

    theme_slug: str | None = Field(
        default=None,
        description="Slug do tema a ser ativado (deve existir na lista de temas do sistema)",
    )
    custom_logo_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL de logo customizada do workspace",
    )
    custom_primary_color: str | None = Field(
        default=None,
        max_length=50,
        description="Cor primária customizada em formato hexadecimal (#RRGGBB) ou RGB",
    )
    custom_css: str | None = Field(
        default=None,
        description="CSS adicional ou regras personalizadas injetadas para o workspace",
    )
    tokens_override: dict[str, Any] | None = Field(
        default=None,
        description="Dicionário de overrides granulares para tokens de cores, geometria ou tipografia",
    )
