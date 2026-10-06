import uuid

import pytest
from httpx import AsyncClient

from src.core.i18n import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    parse_accept_language,
    t,
)


def test_translator_unit_interpolation_and_fallbacks() -> None:
    """Valida o motor de tradução pura, interpolação de variáveis e fallback de chaves."""
    # Teste pt-BR
    assert t("errors.not_found", locale="pt-BR") == "Recurso não encontrado."
    assert (
        t("errors.rate_limit_exceeded", locale="pt-BR", retry_after=45)
        == "Limite de requisições excedido. Tente novamente em 45s."
    )
    assert (
        t("errors.feature_flag_disabled", locale="pt-BR", flag_key="copilot")
        == "A funcionalidade 'copilot' está desabilitada para este workspace."
    )

    # Teste en-US
    assert t("errors.not_found", locale="en-US") == "Resource not found."
    assert (
        t("errors.rate_limit_exceeded", locale="en-US", retry_after=45)
        == "Rate limit exceeded. Please try again in 45s."
    )
    assert (
        t("errors.feature_flag_disabled", locale="en-US", flag_key="copilot")
        == "Feature 'copilot' is disabled for this workspace."
    )

    # Fallback para chave inexistente
    assert t("chave.inexistente", locale="pt-BR") == "chave.inexistente"

    # Fallback para idioma não suportado
    assert t("errors.not_found", locale="ja-JP") == "Recurso não encontrado."


def test_accept_language_parser() -> None:
    """Valida a resolução de pesos 'q-factor' e parsing de cabeçalhos Accept-Language."""
    assert parse_accept_language(None) == DEFAULT_LOCALE
    assert parse_accept_language("") == DEFAULT_LOCALE
    assert parse_accept_language("   ") == DEFAULT_LOCALE

    # Tag direta
    assert parse_accept_language("en-US") == "en-US"
    assert parse_accept_language("en") == "en-US"
    assert parse_accept_language("pt-BR") == "pt-BR"
    assert parse_accept_language("pt") == "pt-BR"

    # Ponderação com q-factor
    assert parse_accept_language("en-US,en;q=0.9,pt-BR;q=0.8") == "en-US"
    assert parse_accept_language("pt-BR;q=0.9,en-US;q=0.5") == "pt-BR"
    assert parse_accept_language("fr-FR;q=1.0,en-US;q=0.8,pt-BR;q=0.3") == "en-US"

    # Idiomas não suportados caem no padrão do framework
    assert parse_accept_language("fr-FR,de-DE;q=0.9,es;q=0.8") == DEFAULT_LOCALE


@pytest.mark.asyncio
async def test_api_i18n_system_endpoint_and_headers(client: AsyncClient) -> None:
    """Valida o endpoint de diagnóstico /system/i18n e cabeçalho Content-Language na resposta."""
    # 1. Requisição com idioma padrão (sem header Accept-Language)
    resp_default = await client.get("/api/v1/system/i18n")
    assert resp_default.status_code == 200
    assert resp_default.headers["Content-Language"] == "pt-BR"
    data_default = resp_default.json()
    assert data_default["current_locale"] == "pt-BR"
    assert "SoftForge" in data_default["welcome_message"]

    # 2. Requisição explícita em inglês (en-US)
    resp_en = await client.get(
        "/api/v1/system/i18n",
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    assert resp_en.status_code == 200
    assert resp_en.headers["Content-Language"] == "en-US"
    data_en = resp_en.json()
    assert data_en["current_locale"] == "en-US"
    assert "Welcome to SoftForge" in data_en["welcome_message"]
    assert set(SUPPORTED_LOCALES).issubset(set(data_en["supported_locales"]))


@pytest.mark.asyncio
async def test_api_error_translation_via_accept_language(client: AsyncClient) -> None:
    """Valida a tradução automática de erros JSON com base no cabeçalho Accept-Language."""
    # Autenticação de usuário para endpoints protegidos
    email = f"i18n_user_{uuid.uuid4().hex[:6]}@softforge.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "i18n User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]

    nonexistent_id = uuid.uuid4()

    # Erro 404 em Inglês (en-US)
    resp_en = await client.get(
        f"/api/v1/system/features/{nonexistent_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    assert resp_en.status_code == 404
    assert resp_en.headers["Content-Language"] == "en-US"
    assert "not found" in resp_en.json()["message"]

    # Erro 404 em Português (pt-BR)
    resp_pt = await client.get(
        f"/api/v1/system/features/{nonexistent_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    assert resp_pt.status_code == 404
    assert resp_pt.headers["Content-Language"] == "pt-BR"
    assert "não encontrada" in resp_pt.json()["message"]
