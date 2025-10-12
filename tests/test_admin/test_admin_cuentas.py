# tests/test_admin/test_admin_cuentas.py
from __future__ import annotations

import pytest
from typing import Optional
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database.db_postgres import SessionLocal
from models.usuario import Usuario
from models.cuenta import Cuenta
from core.enums import EstadoCuenta
from core.seguridad import crear_token

# =============================================================================
# 🎯 Usuarios sembrados por init_seed() (fixture global de conftest)
# =============================================================================
SEED_ADMIN_EMAIL: str = "admin@sistemabancario.com"
SEED_EMISOR_EMAIL: str = "emisor@test.com"
SEED_RECEPTOR_EMAIL: str = "receptor@test.com"

client: TestClient = TestClient(app)


# =============================================================================
# 🔧 Helper — genera un token JWT válido
# =============================================================================
def _token_para_usuario(email: str) -> str:
    """
    Genera un JWT válido con los datos actuales del usuario.
    Se usa en lugar de login para evitar dependencia de contraseñas.
    """
    db: Session = SessionLocal()
    try:
        usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en la BD."
        payload: dict[str, int|str]= {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
        }
        return crear_token(payload)
    finally:
        db.close()


# =============================================================================
# 1️⃣ Admin cambia correctamente el estado de una cuenta
# =============================================================================
def test_admin_actualiza_estado_cuenta_ok() -> None:
    db: Session = SessionLocal()
    try:
        # Tomamos una cuenta real (por ejemplo la del emisor)
        emisor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_EMISOR_EMAIL).first()
        cuenta: Cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == emisor.id).first()
        cuenta_id: int = cuenta.id
    finally:
        db.close()

    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, str] = {"nuevo_estado": "congelada"}

    r = client.put(f"/admin/cuentas/{cuenta_id}/estado", headers=headers, json=payload)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert data["id"] == cuenta_id
    assert data["estado"] in ("congelada", EstadoCuenta.congelada.value)

    # Dejamos la cuenta activa para no afectar otros tests
    payload_back: dict[str, str] = {"nuevo_estado": "activa"}
    r2 = client.put(f"/admin/cuentas/{cuenta_id}/estado", headers=headers, json=payload_back)
    assert r2.status_code == status.HTTP_200_OK


# =============================================================================
# 2️⃣ Cuenta inexistente -> 404
# =============================================================================
def test_admin_actualiza_estado_cuenta_inexistente() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, str] = {"nuevo_estado": "congelada"}

    r = client.put("/admin/cuentas/999999/estado", headers=headers, json=payload)
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrada" in r.json()["detail"].lower()


# =============================================================================
# 3️⃣ Usuario NO admin no puede cambiar estado -> 403
# =============================================================================
def test_no_admin_no_puede_actualizar_estado() -> None:
    db: Session = SessionLocal()
    try:
        emisor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_EMISOR_EMAIL).first()
        receptor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        cuenta_receptor: Cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == receptor.id).first()
        cuenta_id: int = cuenta_receptor.id
    finally:
        db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)  # no admin
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, str] = {"nuevo_estado": "congelada"}

    r = client.put(f"/admin/cuentas/{cuenta_id}/estado", headers=headers, json=payload)
    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert "administradores" in r.json()["detail"].lower()


# =============================================================================
# 4️⃣ Admin actualiza saldo correctamente (PATCH)
# =============================================================================
def test_admin_actualiza_saldo_ok() -> None:
    db: Session = SessionLocal()
    try:
        receptor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        cuenta_receptor: Cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == receptor.id).first()
        cuenta_id: int = cuenta_receptor.id
    finally:
        db.close()

    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    nuevo_saldo: float = 777.77
    payload: dict[str, float] = {"saldo": nuevo_saldo}

    r = client.patch(f"/admin/cuentas/{cuenta_id}/saldo", headers=headers, json=payload)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    # el schema CuentaOut suele serializar Decimal como string -> casteamos
    assert float(data["saldo"]) == pytest.approx(nuevo_saldo, rel=1e-6)


# =============================================================================
# 5️⃣ Admin actualiza saldo de cuenta inexistente -> 404
# =============================================================================
def test_admin_actualiza_saldo_cuenta_inexistente() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, float] = {"saldo": 100.0}

    r = client.patch("/admin/cuentas/999999/saldo", headers=headers, json=payload)
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrada" in r.json()["detail"].lower()


# =============================================================================
# 6️⃣ Usuario NO admin no puede actualizar saldo -> 403
# =============================================================================
def test_no_admin_no_puede_actualizar_saldo() -> None:
    db: Session = SessionLocal()
    try:
        emisor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_EMISOR_EMAIL).first()
        cuenta_emisor: Cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == emisor.id).first()
        cuenta_id: int = cuenta_emisor.id
    finally:
        db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)  # no admin
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, float] = {"saldo": 123.45}

    r = client.patch(f"/admin/cuentas/{cuenta_id}/saldo", headers=headers, json=payload)
    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert "administradores" in r.json()["detail"].lower()


# =============================================================================
# 7️⃣ Validación: saldo inválido (negativo) -> 422 Pydantic
# =============================================================================
@pytest.mark.parametrize("saldo_invalido", [-1, -50.5])
def test_admin_actualiza_saldo_invalido_422(saldo_invalido: float) -> None:
    db: Session = SessionLocal()
    try:
        receptor: Usuario = db.query(Usuario).filter(Usuario.email == SEED_RECEPTOR_EMAIL).first()
        cuenta_receptor: Cuenta = db.query(Cuenta).filter(Cuenta.usuario_id == receptor.id).first()
        cuenta_id: int = cuenta_receptor.id
    finally:
        db.close()

    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, float] = {"saldo": saldo_invalido}

    r = client.patch(f"/admin/cuentas/{cuenta_id}/saldo", headers=headers, json=payload)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = r.json()["detail"]
    # Puede venir como lista de errores de validación
    if isinstance(detail, list):
        assert any("saldo" in str(item.get("loc", [""])[-1]).lower() for item in detail)
    else:
        assert "saldo" in str(detail).lower() or "validación" in str(detail).lower()
