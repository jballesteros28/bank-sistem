# tests/test_admin/test_admin_reportes.py
from __future__ import annotations

import pytest
from typing import Optional
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database.db_postgres import SessionLocal
from models.usuario import Usuario
from core.seguridad import crear_token

# =============================================================================
# 🎯 Usuarios sembrados por init_seed() (fixture global de conftest)
# =============================================================================
SEED_ADMIN_EMAIL: str = "admin@sistemabancario.com"
SEED_EMISOR_EMAIL: str = "emisor@test.com"

client: TestClient = TestClient(app)


# =============================================================================
# 🔧 Helper — genera un token JWT válido
# =============================================================================
def _token_para_usuario(email: str) -> str:
    db: Session = SessionLocal()
    try:
        usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en la BD."
        payload: dict[str, int | str] = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
        }
        return crear_token(payload)
    finally:
        db.close()


# =============================================================================
# 1️⃣ Solo admin puede acceder a los reportes
# =============================================================================
@pytest.mark.parametrize("endpoint", [
    "/admin/reportes/transacciones",
    "/admin/reportes/cuentas/estado",
    "/admin/reportes/usuarios/activos",
    "/admin/reportes/cuentas/saldos",
    "/admin/reportes/usuarios/top-transacciones",
])
def test_no_admin_no_puede_acceder_reportes(endpoint: str) -> None:
    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)  # no admin
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    # Algunos endpoints requieren fechas; agregamos dummy params
    if "transacciones" in endpoint:
        hoy: datetime = datetime.utcnow().date()
        desde = (hoy - timedelta(days=30)).isoformat()
        hasta = hoy.isoformat()
        endpoint = f"{endpoint}?desde={desde}&hasta={hasta}"

    r = client.get(endpoint, headers=headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN, r.text
    assert "administradores" in r.json()["detail"].lower()


# =============================================================================
# 2️⃣ Reporte de transacciones entre fechas (admin)
# =============================================================================
def test_reporte_transacciones_entre_fechas_admin() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    hoy: datetime = datetime.utcnow().date()
    desde: str = (hoy - timedelta(days=30)).isoformat()
    hasta: str = hoy.isoformat()

    r = client.get(f"/admin/reportes/transacciones?desde={desde}&hasta={hasta}", headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert all(key in first for key in ("id", "monto", "fecha"))


# =============================================================================
# 3️⃣ Reporte de cuentas por estado
# =============================================================================
def test_reporte_cuentas_por_estado() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/reportes/cuentas/estado", headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert isinstance(data, dict)

    # Importar los valores reales del Enum para validar correctamente
    from core.enums import EstadoCuenta
    estados_validos = {estado.value for estado in EstadoCuenta}

    # Verificamos que todas las claves del resultado sean estados válidos
    assert all(k in estados_validos for k in data.keys())

    # Y que los valores sean numéricos
    assert all(isinstance(v, int) for v in data.values())


# =============================================================================
# 4️⃣ Reporte de usuarios activos
# =============================================================================
def test_reporte_usuarios_activos() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/reportes/usuarios/activos", headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert isinstance(data, dict)
    assert "activos" in data and "inactivos" in data


# =============================================================================
# 5️⃣ Reporte de saldos por tipo de cuenta
# =============================================================================
def test_reporte_saldos_por_tipo_cuenta() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/reportes/cuentas/saldos", headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert isinstance(data, dict)
    assert all(isinstance(v, (int, float)) for v in data.values())


# =============================================================================
# 6️⃣ Top usuarios por transacciones
# =============================================================================
def test_reporte_top_usuarios_transacciones() -> None:
    token: str = _token_para_usuario(SEED_ADMIN_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/reportes/usuarios/top-transacciones", headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    data = r.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert all(key in first for key in ("nombre", "email", "total_transacciones"))
