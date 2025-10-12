# ==========================================================
# 🧩 tests/test_admin_usuarios.py
# Bloque 1 – Administración: Usuarios (roles y permisos)
# ==========================================================

from __future__ import annotations
import pytest
from typing import Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status

from main import app
from database.db_postgres import SessionLocal
from models.usuario import Usuario
from core.seguridad import crear_token

# ==========================================================
# 🎯 Datos base
# ==========================================================
SEED_ADMIN_EMAIL: str = "admin@sistemabancario.com"
SEED_USUARIO_EMAIL: str = "emisor@test.com"

client: TestClient = TestClient(app)


# ==========================================================
# 🔧 Helper – Genera token JWT válido
# ==========================================================
def _token_para_usuario(email: str) -> str:
    """
    Genera un token JWT válido para el usuario según su email.
    """
    db: Session = SessionLocal()
    try:
        usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en la BD."
        payload: dict[str, str | int] = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
        }
        return crear_token(payload)
    finally:
        db.close()


# ==========================================================
# 1️⃣ Listar usuarios – Solo admin puede acceder
# ==========================================================
def test_listar_usuarios_admin() -> None:
    """✅ Admin debe poder listar usuarios con paginación."""
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/usuarios?skip=0&limit=5", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    data: list[dict] = r.json()
    assert isinstance(data, list)
    assert all("email" in u for u in data)


def test_listar_usuarios_no_admin() -> None:
    """🚫 Usuario común no debe poder acceder al listado de usuarios."""
    token: str = _token_para_usuario(SEED_USUARIO_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/usuarios", headers=headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert "acceso restringido" in r.json()["detail"].lower()


# ==========================================================
# 2️⃣ Cambiar rol de usuario – Casos válidos e inválidos
# ==========================================================
def test_cambiar_rol_usuario_admin() -> None:
    """✅ Admin debe poder cambiar el rol de un usuario."""
    db: Session = SessionLocal()
    usuario: Usuario = db.query(Usuario).filter(Usuario.email == SEED_USUARIO_EMAIL).first()
    db.close()

    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, str] = {"nuevo_rol": "admin"}

    r = client.put(f"/admin/usuarios/{usuario.id}/rol", headers=headers, json=payload)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["rol"] == "admin"

    # revertir cambio a "usuario" para mantener consistencia
    payload_revert: dict[str, str] = {"nuevo_rol": "cliente"}
    r_revert = client.put(f"/admin/usuarios/{usuario.id}/rol", headers=headers, json=payload_revert)
    assert r_revert.status_code == status.HTTP_200_OK
    assert r_revert.json()["rol"] == "cliente"


def test_cambiar_propio_rol_prohibido() -> None:
    """🚫 Admin no debe poder cambiar su propio rol."""
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    db: Session = SessionLocal()
    admin: Usuario = db.query(Usuario).filter(Usuario.email == SEED_ADMIN_EMAIL).first()
    db.close()

    payload: dict[str, str] = {"nuevo_rol": "cliente"}
    r = client.put(f"/admin/usuarios/{admin.id}/rol", headers=headers, json=payload)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "no puedes cambiar tu propio rol" in r.json()["detail"].lower()


def test_cambiar_rol_usuario_inexistente() -> None:
    """🚫 Cambiar rol de un usuario inexistente debe devolver 404."""
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, str] = {"nuevo_rol": "admin"}

    r = client.put("/admin/usuarios/999999/rol", headers=headers, json=payload)
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrado" in r.json()["detail"].lower()
