"""Dicionário de traduções em Português do Brasil (pt-BR)."""

MESSAGES: dict[str, str] = {
    # Erros Globais e HTTP
    "errors.bad_request": "Requisição inválida.",
    "errors.unauthorized": "Não autenticado. Forneça credenciais válidas.",
    "errors.forbidden": "Acesso negado para esta operação.",
    "errors.not_found": "Recurso não encontrado.",
    "errors.rate_limit_exceeded": "Limite de requisições excedido. Tente novamente em {retry_after}s.",
    "errors.feature_flag_disabled": "A funcionalidade '{flag_key}' está desabilitada para este workspace.",
    "errors.invalid_credentials": "Credenciais inválidas. Verifique seu e-mail e senha.",
    "errors.email_already_registered": "E-mail já cadastrado no sistema.",
    "errors.workspace_not_found": "Workspace não encontrado.",
    "errors.feature_flag_not_found": "Feature flag com ID '{flag_id}' não encontrada.",
    "errors.feature_flag_key_exists": "Já existe uma feature flag cadastrada com a chave '{key}'.",
    "errors.insufficient_quota": "Cota do plano excedida para o recurso '{resource}'.",
    "errors.upload_too_large": "Arquivo excede o tamanho máximo permitido de {max_mb}MB.",

    # Sistema e Mensagens Gerais
    "system.healthy": "Sistema operacional e saudável.",
    "system.welcome": "Bem-vindo ao SoftForge — Framework Fullstack AI-Native.",

    # Autenticação
    "auth.login_successful": "Login realizado com sucesso.",
    "auth.logout_successful": "Sessão encerrada com sucesso.",
    "auth.registered_successful": "Conta criada com sucesso.",
}
