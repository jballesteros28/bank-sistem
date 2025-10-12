# tests/conftest.py
import os
import pytest
import pytest_asyncio
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database.db_postgres import Base
from core.dependencias import get_db
from init_seed import init_seed
from core.config import settings
import motor.motor_asyncio

# ================================
# 🔧 Configuración DB de test
# ================================
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

engine_test = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)


# ================================
# 🚫 Neutralizar background tasks y logs
# ================================
async def _noop_async(*args, **kwargs):
    """Función vacía que reemplaza tareas externas (emails/logs)."""
    return None


@pytest.fixture(scope="session", autouse=True)
def patch_background_tasks():
    """
    Reemplaza globalmente los enviadores de correo y el guardado de logs
    para evitar dependencias externas (SMTP, Mongo) durante los tests.
    """
    import services.auth_service as auth_svc
    import services.email_service as email_svc
    import services.log_service as log_svc
    import services.reset_password_service as reset_svc
    import services.enviadores_email.reset_password as reset_mail
    import core.excepciones as exc_mod

    # Neutralizar enviadores de correo
    for svc in (auth_svc, email_svc, reset_mail):
        for fn_name in (
            "enviar_email_bienvenida",
            "enviar_email_actividad_sospechosa",
            "enviar_email_reset_password",
            "enviar_email",
        ):
            if hasattr(svc, fn_name):
                setattr(svc, fn_name, _noop_async)

    # Neutralizar logs
    for mod in (auth_svc, log_svc, exc_mod, reset_svc):
        for fn_name in ("guardar_log", "guardar_log_correo"):
            if hasattr(mod, fn_name):
                setattr(mod, fn_name, _noop_async)


# ================================
# 📌 Fixture DB PostgreSQL
# ================================
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crea la base de datos limpia y carga la semilla inicial."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    init_seed()  # 🌱 poblar DB con admin, emisor, receptor y cuentas
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db_session():
    """Provee una sesión nueva para cada test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ================================
# 📌 Cliente síncrono (usado en tests HTTP clásicos)
# ================================
@pytest.fixture()
def client(db_session):
    """Sobrescribe get_db con la sesión de test (cliente síncrono)."""

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


# ================================
# ⚙️ Cliente asíncrono (para tests con Motor / async endpoints)
# ================================
_mongo_client: motor.motor_asyncio.AsyncIOMotorClient | None = None


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Loop persistente para toda la sesión de tests (evita RuntimeError: loop closed)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(_close_mongo_client())
    loop.close()


async def _close_mongo_client() -> None:
    """Cierra el cliente global de MongoDB si existe."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_mongo_client() -> None:
    """Inicializa y mantiene el cliente global de MongoDB."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """Cliente HTTP asíncrono reutilizable para tests (compatible con httpx>=0.28)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client




