"""English (US) translation dictionary (en-US)."""

MESSAGES: dict[str, str] = {
    # Global and HTTP Errors
    "errors.bad_request": "Invalid request.",
    "errors.unauthorized": "Authentication required. Please provide valid credentials.",
    "errors.forbidden": "Access denied for this operation.",
    "errors.not_found": "Resource not found.",
    "errors.rate_limit_exceeded": "Rate limit exceeded. Please try again in {retry_after}s.",
    "errors.feature_flag_disabled": "Feature '{flag_key}' is disabled for this workspace.",
    "errors.invalid_credentials": "Invalid credentials. Please verify your email and password.",
    "errors.email_already_registered": "Email address already registered.",
    "errors.workspace_not_found": "Workspace not found.",
    "errors.feature_flag_not_found": "Feature flag with ID '{flag_id}' not found.",
    "errors.feature_flag_key_exists": "A feature flag with key '{key}' already exists.",
    "errors.insufficient_quota": "Plan quota exceeded for resource '{resource}'.",
    "errors.upload_too_large": "File exceeds maximum allowed size of {max_mb}MB.",

    # System and General
    "system.healthy": "System operational and healthy.",
    "system.welcome": "Welcome to SoftForge — AI-Native Fullstack Framework.",

    # Authentication
    "auth.login_successful": "Login successful.",
    "auth.logout_successful": "Successfully logged out.",
    "auth.registered_successful": "Account created successfully.",
}
