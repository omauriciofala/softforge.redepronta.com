import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.errors import AppException
from src.core.logging import logger
from src.slices.themes.models import WorkspaceTheme
from src.slices.themes.schemas import (
    ThemeAssets,
    ThemeManifest,
    ThemeTokens,
    WorkspaceThemeRead,
    WorkspaceThemeUpdate,
)

DEFAULT_FALLBACK_MANIFEST = ThemeManifest(
    name="SoftForge Default React",
    slug="default-react",
    version="0.1.0",
    engine="react",
    author="SoftForge Core Team",
    description="Tema padrão integrado em React 18, Tailwind CSS e Shadcn/UI.",
    tokens=ThemeTokens(
        colors={
            "primary": "#2563eb",
            "primary_foreground": "#f8fafc",
            "background": "#ffffff",
            "foreground": "#0f172a",
            "card": "#ffffff",
            "card_foreground": "#0f172a",
            "border": "#e2e8f0",
            "muted": "#f1f5f9",
            "muted_foreground": "#64748b",
            "accent": "#f1f5f9",
        },
        typography={
            "font_family": "Inter, system-ui, -apple-system, sans-serif",
            "font_size_base": "16px",
            "line_height": "1.5",
        },
        geometry={
            "border_radius": "0.5rem",
        },
    ),
    assets=ThemeAssets(
        stylesheets=["/src/index.css"],
        scripts=["/src/main.tsx"],
    ),
)


class ThemeService:
    """Serviço de gerenciamento de temas, white-labeling e tokens de design do SoftForge."""

    @staticmethod
    def get_themes_directory() -> Path:
        """Determina o caminho absoluto do diretório de temas do sistema."""
        configured_path = Path(settings.THEMES_DIR)
        if configured_path.is_absolute() and configured_path.exists():
            return configured_path

        # 1. Tentar relativo ao diretório atual de execução (CWD) se contiver manifestos
        cwd_target = (Path.cwd() / configured_path).resolve()
        if cwd_target.is_dir() and any(cwd_target.glob("*/softforge-theme.json")):
            return cwd_target

        # 2. Procurar nos diretórios ancestrais pelo diretório de temas contendo softforge-theme.json
        for parent in Path(__file__).resolve().parents:
            candidate = (parent / configured_path).resolve()
            if candidate.is_dir() and any(candidate.glob("*/softforge-theme.json")):
                return candidate

        return cwd_target

    @classmethod
    def discover_installed_themes(cls) -> list[ThemeManifest]:
        """Varre o diretório de temas e carrega todos os manifestos válidos (softforge-theme.json)."""
        themes_dir = cls.get_themes_directory()
        manifests: list[ThemeManifest] = []

        if themes_dir.exists() and themes_dir.is_dir():
            for subpath in themes_dir.iterdir():
                if not subpath.is_dir():
                    continue
                manifest_file = subpath / "softforge-theme.json"
                if manifest_file.is_file():
                    try:
                        content = manifest_file.read_text(encoding="utf-8")
                        raw_data = json.loads(content)
                        manifest = ThemeManifest.model_validate(raw_data)
                        manifests.append(manifest)
                    except Exception as exc:
                        logger.warning(
                            f"Falha ao carregar manifesto de tema em '{manifest_file}': {exc}"
                        )

        # Se nenhum tema for encontrado (ex: ambiente de teste isolado), inclui o fallback oficial
        if not manifests:
            manifests.append(DEFAULT_FALLBACK_MANIFEST)

        # Ordena alfabeticamente por slug para consistência
        manifests.sort(key=lambda m: m.slug)
        return manifests

    @classmethod
    def get_theme_by_slug(cls, slug: str) -> ThemeManifest | None:
        """Recupera o manifesto de um tema específico pelo seu identificador (slug)."""
        for theme in cls.discover_installed_themes():
            if theme.slug == slug:
                return theme
        return None

    @classmethod
    def generate_css_variables(
        cls,
        tokens_map: dict[str, Any],
        custom_primary_color: str | None = None,
    ) -> dict[str, str]:
        """Converte o mapa de design tokens em variáveis CSS universais padrão (:root)."""
        colors = tokens_map.get("colors", {}) if isinstance(tokens_map, dict) else {}
        geometry = tokens_map.get("geometry", {}) if isinstance(tokens_map, dict) else {}
        typography = tokens_map.get("typography", {}) if isinstance(tokens_map, dict) else {}

        primary = custom_primary_color or colors.get("primary", "#2563eb")
        primary_fg = colors.get("primary_foreground", "#ffffff")
        bg = colors.get("background", "#ffffff")
        fg = colors.get("foreground", "#0f172a")
        card = colors.get("card", "#ffffff")
        card_fg = colors.get("card_foreground", "#0f172a")
        border = colors.get("border", "#e2e8f0")
        muted = colors.get("muted", "#f1f5f9")
        muted_fg = colors.get("muted_foreground", "#64748b")
        accent = colors.get("accent", "#f1f5f9")
        radius = geometry.get("border_radius", "0.5rem")
        font_family = typography.get(
            "font_family", "system-ui, -apple-system, BlinkMacSystemFont, sans-serif"
        )

        return {
            "--sf-color-primary": primary,
            "--sf-color-primary-foreground": primary_fg,
            "--sf-color-bg": bg,
            "--sf-color-text": fg,
            "--sf-color-card": card,
            "--sf-color-card-foreground": card_fg,
            "--sf-color-border": border,
            "--sf-color-muted": muted,
            "--sf-color-muted-foreground": muted_fg,
            "--sf-color-accent": accent,
            "--sf-radius": radius,
            "--sf-font-family": font_family,
        }

    @classmethod
    async def get_or_create_workspace_theme(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> tuple[WorkspaceTheme, bool]:
        """Busca o registro de tema do workspace ou instancia um novo com valores padrão."""
        query = select(WorkspaceTheme).where(WorkspaceTheme.workspace_id == workspace_id)
        result = await session.execute(query)
        theme_record = result.scalar_one_or_none()

        if theme_record:
            return theme_record, False

        new_record = WorkspaceTheme(
            workspace_id=workspace_id,
            theme_slug="default-react",
            tokens_override={},
        )
        session.add(new_record)
        await session.flush()
        return new_record, True

    @classmethod
    async def evaluate_workspace_theme(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> WorkspaceThemeRead:
        """Consolida os tokens e variáveis do tema ativo do workspace, aplicando overrides."""
        query = select(WorkspaceTheme).where(WorkspaceTheme.workspace_id == workspace_id)
        result = await session.execute(query)
        record = result.scalar_one_or_none()

        active_slug = record.theme_slug if record else "default-react"
        custom_logo = record.custom_logo_url if record else None
        custom_primary = record.custom_primary_color if record else None
        custom_css = record.custom_css if record else None
        tokens_override = record.tokens_override if (record and record.tokens_override) else {}

        manifest = cls.get_theme_by_slug(active_slug)
        if not manifest:
            # Fallback para o primeiro tema disponível ou o default oficial
            installed = cls.discover_installed_themes()
            manifest = installed[0] if installed else DEFAULT_FALLBACK_MANIFEST

        # Mesclar tokens do manifesto com os tokens sobrescritos pelo tenant
        base_tokens = manifest.tokens.model_dump()
        consolidated_tokens: dict[str, Any] = {
            "colors": {**base_tokens.get("colors", {})},
            "typography": {**base_tokens.get("typography", {})},
            "geometry": {**base_tokens.get("geometry", {})},
        }

        # Aplica overrides de tokens se existirem
        for section in ("colors", "typography", "geometry"):
            if section in tokens_override and isinstance(tokens_override[section], dict):
                consolidated_tokens[section].update(tokens_override[section])

        # Se custom_primary_color foi informado no modelo, ele tem precedência
        if custom_primary:
            consolidated_tokens["colors"]["primary"] = custom_primary

        css_vars = cls.generate_css_variables(consolidated_tokens, custom_primary)

        return WorkspaceThemeRead(
            workspace_id=workspace_id,
            theme_slug=manifest.slug,
            theme_name=manifest.name,
            theme_engine=manifest.engine,
            custom_logo_url=custom_logo,
            custom_primary_color=custom_primary,
            custom_css=custom_css,
            tokens=consolidated_tokens,
            tokens_override=tokens_override,
            css_variables=css_vars,
        )

    @classmethod
    async def update_workspace_theme(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        data: WorkspaceThemeUpdate,
    ) -> WorkspaceThemeRead:
        """Atualiza a identidade visual, motor ou tokens customizados do workspace."""
        if data.theme_slug is not None:
            manifest = cls.get_theme_by_slug(data.theme_slug)
            if not manifest:
                raise AppException(
                    message=f"Tema com slug '{data.theme_slug}' não encontrado no sistema.",
                    code="THEME_NOT_FOUND",
                    status_code=400,
                )

        theme_record, _ = await cls.get_or_create_workspace_theme(session, workspace_id)

        if data.theme_slug is not None:
            theme_record.theme_slug = data.theme_slug
        if data.custom_logo_url is not None:
            theme_record.custom_logo_url = data.custom_logo_url
        if data.custom_primary_color is not None:
            theme_record.custom_primary_color = data.custom_primary_color
        if data.custom_css is not None:
            theme_record.custom_css = data.custom_css
        if data.tokens_override is not None:
            theme_record.tokens_override = data.tokens_override

        await session.commit()
        await session.refresh(theme_record)

        return await cls.evaluate_workspace_theme(session, workspace_id)
