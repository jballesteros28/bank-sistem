from __future__ import annotations

import pytest
from pydantic import ValidationError

import scripts.dev_seed as dev_seed
import scripts.reset_local_db as reset_local_db
from app.core.config import DEFAULT_DATABASE_URL, Settings


def test_settings_parse_cors_origins_csv() -> None:
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,https://wallet-demo.vercel.app",
    )

    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://wallet-demo.vercel.app",
    ]


def test_settings_production_rejects_weak_secret_key() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql+psycopg2://wallet:secret@db.example.com:5432/wallet_saas_prod",
            SECRET_KEY="change-me",
            CORS_ORIGINS="https://wallet-demo.vercel.app",
        )


def test_settings_production_requires_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="",
            SECRET_KEY="prod-secret-key-with-enough-entropy-123",
            CORS_ORIGINS="https://wallet-demo.vercel.app",
        )


def test_settings_production_rejects_default_local_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL=DEFAULT_DATABASE_URL,
            SECRET_KEY="prod-secret-key-with-enough-entropy-123",
            CORS_ORIGINS="https://wallet-demo.vercel.app",
        )


def test_settings_production_rejects_cors_wildcard() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql+psycopg2://wallet:secret@db.example.com:5432/wallet_saas_prod",
            SECRET_KEY="prod-secret-key-with-enough-entropy-123",
            CORS_ORIGINS="*",
        )


def test_settings_production_rejects_default_local_cors() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql+psycopg2://wallet:secret@db.example.com:5432/wallet_saas_prod",
            SECRET_KEY="prod-secret-key-with-enough-entropy-123",
            CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173",
        )


def test_ready_endpoint_reports_database_available(client) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"] == "ok"


def test_dev_scripts_abort_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dev_seed.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(reset_local_db.settings, "ENVIRONMENT", "production")

    with pytest.raises(SystemExit, match="production"):
        dev_seed._ensure_dev_database_safety()
    with pytest.raises(SystemExit, match="production"):
        reset_local_db._ensure_dev_database_safety()
