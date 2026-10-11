import hashlib
import hmac
import json
import time
from typing import Any


def generate_webhook_signature(
    secret: str,
    payload: dict[str, Any],
    timestamp: int | None = None,
) -> str:
    """Gera o cabeçalho X-SoftForge-Signature com HMAC-SHA256 e timestamp anti-replay."""
    ts = timestamp if timestamp is not None else int(time.time())
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signed_payload = f"{ts}.{payload_str}".encode()
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={signature}"


def verify_webhook_signature(
    secret: str,
    payload: dict[str, Any],
    signature_header: str,
    tolerance_seconds: int = 300,
) -> bool:
    """Verifica se a assinatura recebida é autêntica e dentro da janela de tolerância de tempo (anti-replay)."""
    try:
        parts = dict(part.split("=", 1) for part in signature_header.split(","))
        ts_str = parts.get("t")
        expected_v1 = parts.get("v1")

        if not ts_str or not expected_v1:
            return False

        ts = int(ts_str)
        # Previne ataques de repetição se for mais antigo que a tolerância
        if abs(int(time.time()) - ts) > tolerance_seconds:
            return False

        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signed_payload = f"{ts}.{payload_str}".encode()
        computed_v1 = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(computed_v1, expected_v1)
    except Exception:
        return False


def validate_webhook_url(url: str, allow_mock: bool = True) -> None:
    """Valida se a URL de webhook é segura, prevenindo ataques SSRF (Server-Side Request Forgery)."""
    import ipaddress
    import urllib.parse

    from src.core.errors import AppException

    if allow_mock and (
        url.startswith("mock://")
        or url.startswith("https://mock.")
        or url.startswith("http://mock.")
    ):
        return

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as exc:
        raise AppException(message="Formato de URL de webhook inválido.", status_code=400) from exc

    if parsed.scheme not in ("http", "https"):
        raise AppException(
            message="URL de webhook deve utilizar protocolo HTTP ou HTTPS.", status_code=400
        )

    hostname = parsed.hostname
    if not hostname:
        raise AppException(message="URL de webhook sem host de destino válido.", status_code=400)

    lowered = hostname.lower()
    if (
        lowered in ("localhost", "127.0.0.1", "::1")
        or lowered.endswith(".local")
        or lowered.endswith(".internal")
    ):
        raise AppException(
            message="Endereço de destino de webhook restrito (SSRF protection: localhost/internal).",
            status_code=400,
        )

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise AppException(
                message="Endereço IP de destino restrito (SSRF protection: redes privadas/reservadas proibidas).",
                status_code=400,
            )
    except ValueError:
        # Hostname é um nome de domínio válido
        pass

