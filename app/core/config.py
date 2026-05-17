from __future__ import annotations

import json
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/wallet_saas"
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
ALLOWED_ENVIRONMENTS = {"development", "testing", "production"}
WEAK_SECRET_KEYS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "secret-key",
    "test",
    "password",
    "wallet-saas",
}
ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _is_weak_secret_key(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in WEAK_SECRET_KEYS or len(value.strip()) < 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Wallet SaaS API"
    APP_VERSION: str = "1.8.0-alpha"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = DEFAULT_DATABASE_URL
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "wallet_saas_logs"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    EMAILS_ENABLED: bool = False
    FRONTEND_URL: str = "http://127.0.0.1:5173"
    BACKEND_URL: str = "http://127.0.0.1:8000"
    LOG_LEVEL: str = "INFO"
    ENABLE_HSTS: bool = False
    CORS_ORIGINS: Annotated[list[str], NoDecode] = DEFAULT_CORS_ORIGINS

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value or "false").strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug"}:
            return True
        if normalized in {"0", "false", "no", "off", "release"}:
            return False
        raise ValueError("DEBUG debe ser true o false.")

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        environment = str(value or "").strip().lower()
        if environment == "test":
            environment = "testing"
        if environment not in ALLOWED_ENVIRONMENTS:
            allowed = ", ".join(sorted(ALLOWED_ENVIRONMENTS))
            raise ValueError(f"ENVIRONMENT debe ser uno de: {allowed}.")
        return environment

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        level = str(value or "INFO").strip().upper()
        if level not in ALLOWED_LOG_LEVELS:
            allowed = ", ".join(sorted(ALLOWED_LOG_LEVELS))
            raise ValueError(f"LOG_LEVEL debe ser uno de: {allowed}.")
        return level

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | tuple[str, ...] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                try:
                    decoded = json.loads(raw_value)
                except json.JSONDecodeError as exc:
                    raise ValueError("CORS_ORIGINS JSON invalido.") from exc
                if not isinstance(decoded, list):
                    raise ValueError("CORS_ORIGINS JSON debe ser una lista.")
                return [str(origin).strip() for origin in decoded if str(origin).strip()]
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        return [str(origin).strip() for origin in value if str(origin).strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        if self.ENVIRONMENT != "production":
            return self

        if self.DEBUG:
            raise ValueError("DEBUG debe ser false en production.")
        if not self.DATABASE_URL.strip():
            raise ValueError("DATABASE_URL es obligatorio en production.")
        if self.DATABASE_URL.strip() == DEFAULT_DATABASE_URL:
            raise ValueError("DATABASE_URL debe configurarse explicitamente en production.")
        if _is_weak_secret_key(self.SECRET_KEY):
            raise ValueError("SECRET_KEY debe ser fuerte y distinto de valores demo en production.")
        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS es obligatorio en production.")
        if "*" in self.CORS_ORIGINS:
            raise ValueError('CORS_ORIGINS no puede incluir "*" en production.')
        if set(self.CORS_ORIGINS).issubset(set(DEFAULT_CORS_ORIGINS)):
            raise ValueError("CORS_ORIGINS debe incluir al menos un origen frontend de production.")
        return self


settings = Settings()
