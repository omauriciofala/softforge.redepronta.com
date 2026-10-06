from collections.abc import Callable
from contextvars import ContextVar

from src.core.errors import ForbiddenException
from src.slices.apikeys.models import ApiKey
from src.slices.apikeys.security import has_required_scope

# ContextVar que armazena a chave de API autenticada durante o ciclo de vida da requisição
current_api_key_context: ContextVar[ApiKey | None] = ContextVar("current_api_key_context", default=None)


def get_current_api_key() -> ApiKey | None:
    """Retorna a chave de API autenticada na requisição atual, ou None caso autenticado via JWT/Sessão."""
    return current_api_key_context.get()


def require_api_key_scope(required_scope: str) -> Callable[..., bool]:
    """
    Fábrica de dependências que valida se a chave de API utilizada possui o escopo necessário.
    Se o cliente estiver autenticado via JWT interativo (usuário na interface web), a restrição de escopo de PAT não se aplica.
    """

    def _scope_checker() -> bool:
        api_key = get_current_api_key()
        if api_key and not has_required_scope(api_key.scopes, required_scope):
            raise ForbiddenException(
                message=f"Esta chave de API não possui o escopo necessário: '{required_scope}'."
            )
        return True

    return _scope_checker
