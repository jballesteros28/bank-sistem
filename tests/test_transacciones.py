from __future__ import annotations

import pytest
from decimal import Decimal
from typing import Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database.db_postgres import SessionLocal
from models.cuenta import Cuenta
from models.usuario import Usuario
from core.enums import EstadoCuenta
from core.seguridad import crear_token


# ==========================================================
# 🎯 Usuarios sembrados por init_seed() (fixture global)
# ==========================================================
SEED_EMISOR_EMAIL: str = "emisor@test.com"
SEED_RECEPTOR_EMAIL: str = "receptor@test.com"

client: TestClient = TestClient(app)


# ==========================================================
# 🔧 Helper local — genera un token JWT válido
# ==========================================================
def _token_para_usuario(email: str) -> str:
    """
    Genera un JWT válido con los datos actuales del usuario.
    Se usa en lugar de login para evitar dependencia de contraseñas.
    """
    db: Session = SessionLocal()
    try:
        usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en la BD."
        payload = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
        }
        return crear_token(payload)
    finally:
        db.close()


# ==========================================================
# 1️⃣ Transferencia exitosa
# ==========================================================
def test_transferencia_exitosa(client: TestClient) -> None:
    """✅ Debe permitir transferir dinero correctamente entre cuentas activas."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    receptor: Usuario = db.query(Usuario).filter_by(email=SEED_RECEPTOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    cuenta_destino: Cuenta = db.query(Cuenta).filter_by(usuario_id=receptor.id).first()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_destino.id,
        "monto": 100,
        "tipo": "transferencia",
        "descripcion": "Test transferencia exitosa",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen.id}", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert float(data["monto"]) == 100.00  # JSON convierte Decimal a str
    assert data["estado"] == "completada"


# ==========================================================
# 2️⃣ Saldo insuficiente
# ==========================================================
def test_transferencia_saldo_insuficiente(client: TestClient) -> None:
    """🚫 Debe rechazar la transferencia si el saldo es insuficiente."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    receptor: Usuario = db.query(Usuario).filter_by(email=SEED_RECEPTOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    cuenta_destino: Cuenta = db.query(Cuenta).filter_by(usuario_id=receptor.id).first()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_destino.id,
        "monto": 999999,  # monto mayor al saldo disponible
        "tipo": "transferencia",
        "descripcion": "Test saldo insuficiente",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen.id}", headers=headers, json=payload)
    assert r.status_code in (400, 422)
    assert "saldo" in r.json()["detail"].lower()


# ==========================================================
# 3️⃣ Cuenta origen congelada
# ==========================================================
def test_transferencia_cuenta_origen_congelada(client: TestClient) -> None:
    """🚫 Debe rechazar transferencias desde cuentas congeladas."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    receptor: Usuario = db.query(Usuario).filter_by(email=SEED_RECEPTOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    cuenta_destino: Cuenta = db.query(Cuenta).filter_by(usuario_id=receptor.id).first()

    cuenta_origen_id: int = cuenta_origen.id
    cuenta_destino_id: int = cuenta_destino.id

    cuenta_origen.estado = EstadoCuenta.congelada
    db.commit()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_destino_id,
        "monto": 50,
        "tipo": "transferencia",
        "descripcion": "Origen congelada",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen_id}", headers=headers, json=payload)
    assert r.status_code == 403
    assert "origen" in r.json()["detail"].lower()

    # Reactivar cuenta después del test
    db = SessionLocal()
    cuenta_origen = db.get(Cuenta, cuenta_origen_id)
    cuenta_origen.estado = EstadoCuenta.activa
    db.commit()
    db.close()


# ==========================================================
# 4️⃣ Cuenta destino congelada
# ==========================================================
def test_transferencia_cuenta_destino_congelada(client: TestClient) -> None:
    """🚫 Debe rechazar transferencias hacia cuentas congeladas."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    receptor: Usuario = db.query(Usuario).filter_by(email=SEED_RECEPTOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    cuenta_destino: Cuenta = db.query(Cuenta).filter_by(usuario_id=receptor.id).first()

    cuenta_origen_id: int = cuenta_origen.id
    cuenta_destino_id: int = cuenta_destino.id

    cuenta_destino.estado = EstadoCuenta.congelada
    db.commit()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_destino_id,
        "monto": 50,
        "tipo": "transferencia",
        "descripcion": "Destino congelada",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen_id}", headers=headers, json=payload)
    assert r.status_code == 403
    assert "destino" in r.json()["detail"].lower()

    # Reactivar cuenta después del test
    db = SessionLocal()
    cuenta_destino = db.get(Cuenta, cuenta_destino_id)
    cuenta_destino.estado = EstadoCuenta.activa
    db.commit()
    db.close()


# ==========================================================
# 5️⃣ Cuenta destino inexistente
# ==========================================================
def test_transferencia_cuenta_inexistente(client: TestClient) -> None:
    """🚫 Debe devolver 404 si la cuenta destino no existe."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": 999999,
        "monto": 10,
        "tipo": "transferencia",
        "descripcion": "Destino inexistente",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen.id}", headers=headers, json=payload)
    assert r.status_code == 404
    detail: str = r.json()["detail"].lower()
    assert "no encontrada" in detail or "no está disponible" in detail


# ==========================================================
# 6️⃣ Historial del usuario
# ==========================================================
def test_historial_transacciones(client: TestClient) -> None:
    """📜 Debe devolver el historial de transacciones del usuario autenticado."""
    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    r = client.get("/transacciones/historial", headers=headers)
    assert r.status_code == 200
    data: list[dict] = r.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "monto" in data[0]


# ==========================================================
# 7️⃣ Token inválido o expirado
# ==========================================================
def test_transferencia_token_invalido(client: TestClient) -> None:
    """🔒 Debe devolver 401 si el token es inválido o manipulado."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    db.close()

    headers: dict[str, str] = {"Authorization": "Bearer token-falso"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_origen.id,
        "monto": 10,
        "tipo": "transferencia",
        "descripcion": "Token inválido",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen.id}", headers=headers, json=payload)
    assert r.status_code == 401
    assert "inválido" in r.json()["detail"].lower() or "expirado" in r.json()["detail"].lower()


# ==========================================================
# 8️⃣ Monto igual a cero o negativo
# ==========================================================
@pytest.mark.parametrize("monto", [0, -50])
def test_transferencia_monto_invalido(client: TestClient, monto: float) -> None:
    """🚫 Debe rechazar montos iguales o menores a cero."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    receptor: Usuario = db.query(Usuario).filter_by(email=SEED_RECEPTOR_EMAIL).first()
    cuenta_origen: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    cuenta_destino: Cuenta = db.query(Cuenta).filter_by(usuario_id=receptor.id).first()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta_destino.id,
        "monto": monto,
        "tipo": "transferencia",
        "descripcion": f"Monto inválido {monto}",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta_origen.id}", headers=headers, json=payload)
    assert r.status_code in (400, 422)

    detail = r.json()["detail"]
    if isinstance(detail, list):
        assert any("monto" in str(item["loc"][-1]).lower() for item in detail)
    else:
        # Acepta tanto validación de campo como error genérico
        assert any(
            palabra in detail.lower()
            for palabra in ["monto", "validación", "datos"]
        )



# ==========================================================
# 9️⃣ Transferencia a misma cuenta
# ==========================================================
def test_transferencia_misma_cuenta(client: TestClient) -> None:
    """🚫 Debe devolver error si la cuenta origen y destino son la misma."""
    db: Session = SessionLocal()
    emisor: Usuario = db.query(Usuario).filter_by(email=SEED_EMISOR_EMAIL).first()
    cuenta: Cuenta = db.query(Cuenta).filter_by(usuario_id=emisor.id).first()
    db.close()

    token: str = _token_para_usuario(SEED_EMISOR_EMAIL)
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    payload: dict[str, object] = {
        "cuenta_destino_id": cuenta.id,
        "monto": 10,
        "tipo": "transferencia",
        "descripcion": "Misma cuenta",
    }

    r = client.post(f"/transacciones/?cuenta_origen_id={cuenta.id}", headers=headers, json=payload)
    assert r.status_code in (400, 403, 422)
