# tests/test_cuentas.py
from __future__ import annotations

from typing import Final
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from database.db_postgres import SessionLocal
from models.usuario import Usuario
from models.cuenta import Cuenta
from core.seguridad import crear_token
from core.enums import TipoCuenta

# 🎯 Usuarios sembrados por init_seed()
SEED_EMISOR_EMAIL: Final[str] = "emisor@test.com"
SEED_RECEPTOR_EMAIL: Final[str] = "receptor@test.com"


# ==========================================================
# 🔧 Helper: genera un token JWT válido para un usuario
# ==========================================================
def _token_para_usuario(email: str) -> str:
    """
    Genera un JWT válido con expiración a 30 min.
    Se usa en lugar de login real para evitar dependencias.
    """
    db: Session = SessionLocal()
    try:
        usuario: Usuario | None = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en seed"
        payload = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        return crear_token(payload)
    finally:
        db.close()


# ==========================================================
# ✅ 1. Crear cuenta bancaria (happy path)
# ==========================================================
def test_crear_cuenta_ok(client: TestClient) -> None:
    """Debe permitir crear una cuenta nueva de tipo 'ahorro'."""
    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"tipo": "corriente"}
    r = client.post("/cuentas/", headers=headers, json=payload)

    assert r.status_code == 201, r.text
    body = r.json()

    assert body["tipo"] == "corriente"
    assert body["saldo"] == "0.00"
    assert body["estado"] == "activa"
    assert body["numero"].startswith("CTA-")


# ==========================================================
# 🚫 2. Rechazar duplicado de tipo de cuenta
# ==========================================================
def test_crear_cuenta_duplicada(client: TestClient) -> None:
    """Debe impedir crear otra cuenta del mismo tipo (400)."""
    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"tipo": "ahorro"}
    r = client.post("/cuentas/", headers=headers, json=payload)

    # Ya existe una cuenta de ahorro creada en el test anterior
    assert r.status_code == 400
    assert "ya tienes" in r.json()["detail"].lower()


# ==========================================================
# ✅ 3. Listar todas las cuentas del usuario
# ==========================================================
def test_listar_cuentas_ok(client: TestClient) -> None:
    """Debe devolver al menos una cuenta del usuario autenticado."""
    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/cuentas/", headers=headers)
    assert r.status_code == 200, r.text

    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "tipo" in body[0]
    assert "numero" in body[0]


# ==========================================================
# ✅ 4. Consultar una cuenta específica propia
# ==========================================================
def test_obtener_cuenta_ok(client: TestClient) -> None:
    """Debe poder consultar una cuenta propia."""
    db: Session = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == SEED_EMISOR_EMAIL).first()
        cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == usuario.id).first()
        assert cuenta is not None, "No se encontró cuenta en la DB para el emisor"
        cuenta_id = cuenta.id
    finally:
        db.close()

    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get(f"/cuentas/{cuenta_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == cuenta_id


# ==========================================================
# 🚫 5. Consultar cuenta ajena → debe dar 404
# ==========================================================
def test_obtener_cuenta_ajena(client: TestClient) -> None:
    """Debe rechazar el acceso a cuentas de otro usuario."""
    db: Session = SessionLocal()
    try:
        # Obtenemos una cuenta del receptor (otro usuario)
        receptor = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        cuenta_receptor = db.query(Cuenta).filter(Cuenta.usuario_id == receptor.id).first()
        assert cuenta_receptor is not None
        cuenta_id = cuenta_receptor.id
    finally:
        db.close()

    token = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get(f"/cuentas/{cuenta_id}", headers=headers)
    assert r.status_code == 404
    assert (
        "no pertenece" in r.json()["detail"].lower()
        or "no encontrada" in r.json()["detail"].lower()
        or "no existe" in r.json()["detail"].lower()
    )


# ==========================================================
# 🚫 6. Token inválido → debe devolver 401
# ==========================================================
def test_cuenta_token_invalido(client: TestClient) -> None:
    """No debe permitir acceso con token falso."""
    headers = {"Authorization": "Bearer token-falso"}
    r = client.get("/cuentas/", headers=headers)

    assert r.status_code == 401
    assert "inválido" in r.json()["detail"].lower() or "expirado" in r.json()["detail"].lower()
