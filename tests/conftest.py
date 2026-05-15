from __future__ import annotations

import os
from collections.abc import Generator
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["APP_NAME"] = "Wallet SaaS API"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./wallet_saas_test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

from app.apps.organizaciones.models import Organizacion
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.core.database import Base, assert_test_database_url, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.shared.enums import EstadoOrganizacion, EstadoWallet, MonedaWallet, RolUsuario, TipoWallet


TEST_DATABASE_URL = os.environ["DATABASE_URL"]
assert_test_database_url(TEST_DATABASE_URL)

engine_test = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
TestingSessionLocal = sessionmaker(bind=engine_test, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    assert_test_database_url(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def api_data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token({"sub": str(usuario.id), "email": usuario.email, "rol": usuario.rol.value})
    return {"Authorization": f"Bearer {token}"}


def create_org(db: Session, slug: str | None = None) -> Organizacion:
    suffix = uuid4().hex[:8]
    org = Organizacion(
        nombre=f"Org {suffix}",
        slug=slug or f"org-{suffix}",
        email_contacto=f"contacto-{suffix}@example.com",
        estado=EstadoOrganizacion.activa,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def create_user(
    db: Session,
    org: Organizacion | None,
    role: RolUsuario = RolUsuario.cliente,
    password: str = "Password123!",
) -> Usuario:
    suffix = uuid4().hex[:8]
    user = Usuario(
        nombre=f"Usuario {suffix}",
        email=f"user-{suffix}@example.com",
        hashed_password=hash_password(password),
        rol=role,
        es_activo=True,
        organizacion_id=org.id if org else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_wallet(
    db: Session,
    user: Usuario,
    *,
    saldo: Decimal = Decimal("0.00"),
    moneda: MonedaWallet = MonedaWallet.ARS,
    estado: EstadoWallet = EstadoWallet.activa,
    es_principal: bool = False,
) -> Wallet:
    wallet = Wallet(
        alias=f"Wallet {uuid4().hex[:6]}",
        tipo=TipoWallet.principal,
        moneda=moneda,
        estado=estado,
        saldo=saldo,
        es_principal=es_principal,
        usuario_id=user.id,
        organizacion_id=user.organizacion_id,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def onboarding_payload(slug: str | None = None, email: str | None = None) -> dict[str, object]:
    suffix = uuid4().hex[:8]
    return {
        "organizacion": {
            "nombre": f"Tenant {suffix}",
            "slug": slug or f"tenant-{suffix}",
            "email_contacto": f"contacto-{suffix}@example.com",
        },
        "owner": {
            "nombre": f"Owner {suffix}",
            "email": email or f"owner-{suffix}@example.com",
            "password": "Password123!",
        },
    }

