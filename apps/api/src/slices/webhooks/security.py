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
