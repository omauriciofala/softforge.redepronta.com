import re
from contextvars import ContextVar
from typing import Any

from src.core.i18n.locales.en_us import MESSAGES as EN_US_MESSAGES
from src.core.i18n.locales.pt_br import MESSAGES as PT_BR_MESSAGES

SUPPORTED_LOCALES: tuple[str, ...] = ("pt-BR", "en-US")
DEFAULT_LOCALE: str = "pt-BR"

CATALOGS: dict[str, dict[str, str]] = {
    "pt-BR": PT_BR_MESSAGES,
    "en-US": EN_US_MESSAGES,
}

_current_locale_var: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)


def get_current_locale() -> str:
    """Retorna o idioma ativo no contexto da requisição atual."""
    return _current_locale_var.get()


def set_current_locale(locale: str) -> None:
    """Define o idioma ativo no contexto assíncrono."""
    if locale in SUPPORTED_LOCALES:
        _current_locale_var.set(locale)
    else:
        _current_locale_var.set(DEFAULT_LOCALE)


def parse_accept_language(header: str | None) -> str:
    """
    Analisa o cabeçalho HTTP 'Accept-Language' conforme RFC 7231.
    Retorna 'pt-BR' ou 'en-US' com base na ponderação de qualidade (q-factor).
    """
    if not header or not header.strip():
        return DEFAULT_LOCALE

    # Divide por vírgulas: ex. "en-US,en;q=0.9,pt-BR;q=0.8"
    candidates: list[tuple[float, str]] = []

    for item in header.split(","):
        item = item.strip()
        if not item:
            continue

        parts = item.split(";")
        lang_tag = parts[0].strip().lower().replace("_", "-")
        q = 1.0

        if len(parts) > 1:
            for param in parts[1:]:
                param = param.strip()
                match = re.match(r"^q=([0-9.]+)", param)
                if match:
                    try:
                        q = float(match.group(1))
                    except ValueError:
                        q = 0.0

        candidates.append((q, lang_tag))

    # Ordena por prioridade 'q' decrescente
    candidates.sort(key=lambda x: x[0], reverse=True)

    for _, tag in candidates:
        if tag.startswith("en"):
            return "en-US"
        if tag.startswith("pt"):
            return "pt-BR"

    return DEFAULT_LOCALE


def t(key: str, locale: str | None = None, **kwargs: Any) -> str:
    """
    Traduz uma chave para o idioma solicitado ou o idioma ativo no contexto da requisição.
    Suporta interpolação segura de parâmetros como {retry_after} ou {flag_key}.
    """
    active_locale = locale or get_current_locale()
    catalog = CATALOGS.get(active_locale, CATALOGS[DEFAULT_LOCALE])

    template = catalog.get(key)
    if template is None and active_locale != DEFAULT_LOCALE:
        # Fallback para o idioma padrão
        template = CATALOGS[DEFAULT_LOCALE].get(key)

    if template is None:
        return key

    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    return template


def get_translations_catalog(locale: str | None = None) -> dict[str, str]:
    """Retorna o catálogo completo de mensagens traduzidas para o idioma selecionado."""
    active_locale = locale or get_current_locale()
    return dict(CATALOGS.get(active_locale, CATALOGS[DEFAULT_LOCALE]))
