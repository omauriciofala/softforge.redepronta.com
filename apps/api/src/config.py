from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ambiente
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Servidor
    PROJECT_NAME: str = "SoftForge API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Segurança & JWT
    SECRET_KEY: str = "dev-insecure-secret-key-32-chars-minimum!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Banco de Dados
    DATABASE_URL: str = (
        "postgresql+asyncpg://softforge:softforge_secret@localhost:5432/softforge_db"
    )

    # CORS & Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # OAuth2 Social Login
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Redis & Background Workers (Arq)
    REDIS_URL: str = "redis://localhost:6379/0"
    WORKER_BURST: bool = False

    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: Literal["colored", "json"] = "colored"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
