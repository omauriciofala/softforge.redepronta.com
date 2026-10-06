import hashlib
import secrets


def hash_api_key(raw_key: str) -> str:
    """Calcula o hash seguro SHA-256 da chave de API em texto puro."""
    return hashlib.sha256(raw_key.strip().encode()).hexdigest()


def generate_api_key(prefix: str = "sf_live_") -> tuple[str, str, str]:
    """
    Gera uma chave de API criptograficamente segura.

    Retorna uma tupla contendo:
    - raw_key: chave em texto puro (exibida apenas uma vez ao usuário)
    - key_prefix: identificador mascarado para exibição e conferência
    - hashed_key: hash SHA-256 para persistência segura no banco
    """
    token_entropy = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{token_entropy}"
    key_prefix = f"{raw_key[:12]}...{raw_key[-4:]}"
    hashed_key = hash_api_key(raw_key)
    return raw_key, key_prefix, hashed_key


def has_required_scope(granted_scopes: list[str], required_scope: str) -> bool:
    """
    Valida se os escopos atribuídos à chave de API atendem ao escopo exigido.

    Suporta:
    - Escopo universal: '*'
    - Correspondência exata: 'projects:read' == 'projects:read'
    - Correspondência com curinga de namespace: 'projects:*' satisfaz 'projects:read' e 'projects:write'
    """
    if "*" in granted_scopes:
        return True

    if required_scope in granted_scopes:
        return True

    for scope in granted_scopes:
        if scope.endswith(":*"):
            namespace = scope[:-2]
            if required_scope.startswith(f"{namespace}:"):
                return True

    return False
