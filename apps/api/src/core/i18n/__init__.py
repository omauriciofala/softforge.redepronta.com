"""Módulo de Internacionalização (i18n) do SoftForge."""

from src.core.i18n.translator import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    get_current_locale,
    get_translations_catalog,
    parse_accept_language,
    set_current_locale,
    t,
)

__all__ = [
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
    "get_current_locale",
    "get_translations_catalog",
    "parse_accept_language",
    "set_current_locale",
    "t",
]
