# tests/test_usuario_actual.py
from __future__ import annotations

from typing import Final
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from database.db_postgres import SessionLocal
from models.usuario import Usuario
from core.seguridad import crear_token
from typing import Any

# 🎯 Usuarios sembrados por init_seed()
SEED_EMISOR_EMAIL: Final[str] = "emisor@test.com"
SEED_RECEPTOR_EMAIL: Final[str] = "receptor@test.com"
SEED_PASSWORD: Final[str] = "pass1234"  # Solo se usa si el login vuelve a ser necesario


# ==========================================================
# 🔧 Helper: genera un token válido desde la DB real
# ==========================================================
def _token_para_usuario(email: str) -> str:
    """
    Genera un JWT válido con datos actuales del usuario.
    Se usa en lugar de login para evitar dependencia de contraseñas
    (que pueden modificarse en otros tests).
    """
    db: Session = SessionLocal()
    try:
        usuario: Usuario | None = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en seed"
        payload: dict[str, Any] = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),  # ✅ UTC-aware
        }
        return crear_token(payload)
    finally:
        db.close()


# ==========================================================
# ✅ Happy path
# ==========================================================
def test_usuario_actual_ok(client: TestClient) -> None:
    """
    Debe devolver el perfil del usuario 'emisor@test.com' sembrado por init_seed().
    """
    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/usuarios/me", headers=headers)
    assert r.status_code == 200, r.text

    body = r.json()
    assert body["email"] == SEED_EMISOR_EMAIL
    assert body["es_activo"] is True
    assert "id" in body and "nombre" in body and "rol" in body


# ==========================================================
# 🚫 Casos negativos
# ==========================================================
def test_usuario_actual_sin_token(client: TestClient) -> None:
    """
    No debe permitir acceso sin token JWT.
    """
    r = client.get("/usuarios/me")
    assert r.status_code == 401
    assert "not authenticated" in r.text.lower()


def test_usuario_actual_token_invalido(client: TestClient) -> None:
    """
    Token completamente inválido → debe devolver 401.
    """
    headers = {"Authorization": "Bearer token-falso"}
    r = client.get("/usuarios/me", headers=headers)
    assert r.status_code == 401
    assert "inválido" in r.json()["detail"].lower() or "expirado" in r.json()["detail"].lower()


def test_usuario_actual_token_expirado(client: TestClient) -> None:
    """
    Token expirado (exp < ahora) → debe devolver 401.
    """
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == SEED_EMISOR_EMAIL).first()
        assert usuario is not None
        payload: dict[str, Any]= {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),  # ✅ token realmente expirado
        }
        token_expirado = crear_token(payload)
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {token_expirado}"}
    r = client.get("/usuarios/me", headers=headers)
    assert r.status_code == 401
    assert "expirado" in r.json()["detail"].lower() or "inválido" in r.json()["detail"].lower()


def test_usuario_actual_usuario_inexistente(client: TestClient) -> None:
    """
    Genera un JWT válido pero con un user_id que NO existe en la DB.
    Debe devolver 401 por validación de get_current_user().
    """
    fake_user_id: int = 999_999
    payload: dict[str, Any] = {
        "id": fake_user_id,
        "email": "fake@test.com",
        "nombre": "No Existe",
        "rol": "cliente",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),  # ✅ UTC-aware
    }
    token = crear_token(payload)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/usuarios/me", headers=headers)
    assert r.status_code == 401
    assert "inválido" in r.json()["detail"].lower() or "no encontrado" in r.json()["detail"].lower()


def test_usuario_actual_usuario_desactivado(client: TestClient) -> None:
    """
    Desactiva temporalmente al 'receptor@test.com' (seed),
    verifica que no pueda acceder al perfil y luego lo reactiva.
    """
    db: Session = SessionLocal()
    try:
        usuario: Usuario | None = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        assert usuario is not None
        usuario.es_activo = False
        db.add(usuario)
        db.commit()
        user_id = usuario.id
    finally:
        db.close()

    payload: dict[str,Any] = {
        "id": user_id,
        "email": SEED_RECEPTOR_EMAIL,
        "nombre": "Usuario Receptor",
        "rol": "cliente",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),  # ✅ UTC-aware
    }
    token = crear_token(payload)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/usuarios/me", headers=headers)
    # Según implementación, puede ser 401 o 404 (ambos válidos)
    assert r.status_code in (401, 404)
    assert "inactivo" in r.json()["detail"].lower() or "desactivado" in r.json()["detail"].lower()

    # 🔓 Reactivar receptor para no interferir en otros tests
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        assert usuario is not None
        usuario.es_activo = True
        db.add(usuario)
        db.commit()
    finally:
        db.close()
