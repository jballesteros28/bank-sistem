# tests/manual_test_logs.py
import requests
from core.config import settings
from init_seed import init_seed
from services.auth_service import crear_token
from sqlalchemy.orm import Session
from  models.usuario import Usuario
from database.db_postgres import SessionLocal


# =============================
# ⚙️ CONFIG
# =============================
BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "admin@sistemabancario.com"
EMISOR_EMAIL = "emisor@test.com"

# Inicializamos los datos si hace falta
init_seed()


def _token_para_usuario(email: str) -> str:
    """Genera un JWT válido con los mismos claims que usa FastAPI."""
    db: Session = SessionLocal()
    usuario : Usuario = db.query(Usuario).filter(Usuario.email == email).first()
    db.close()
    if not usuario:
        raise ValueError(f"usuario{email} no encontrado")

    payload: dict[str, object] = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }
    return crear_token(payload)
# =============================
# 🔑 Generar tokens
# =============================
admin_token = _token_para_usuario(ADMIN_EMAIL)
emisor_token = _token_para_usuario(EMISOR_EMAIL)

# =============================
# 🧪 Tests manuales de endpoints de logs
# =============================

def test_logs_sistema():
    r = requests.get(
        f"{BASE_URL}/admin/logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print("\n🧾 LOGS SISTEMA:", r.status_code)
    print(r.json())


def test_logs_filtrados():
    r = requests.get(
        f"{BASE_URL}/admin/logs?evento=CambioRolUsuario&nivel=INFO",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print("\n🎯 LOGS FILTRADOS:", r.status_code)
    print(r.json())


def test_logs_correos():
    r = requests.get(
        f"{BASE_URL}/admin/logs/correos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print("\n📬 LOGS DE CORREOS:", r.status_code)
    print(r.json())


def test_logs_correos_limit():
    r = requests.get(
        f"{BASE_URL}/admin/logs/correos?limit=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print("\n📉 LOGS CORREOS (limit 5):", r.status_code)
    print(r.json())


if __name__ == "__main__":
    print("🚀 Iniciando tests manuales de logs...")
    test_logs_sistema()
    test_logs_filtrados()
    test_logs_correos()
    test_logs_correos_limit()
