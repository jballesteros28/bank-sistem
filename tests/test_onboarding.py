from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.enums import EstadoCuenta, RolUsuario
from core.seguridad import crear_token
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario


def _payload(slug: str | None = None, email: str | None = None) -> dict[str, object]:
    sufijo = uuid4().hex[:8]
    slug = slug or f"onboarding-{sufijo}"
    email = email or f"owner-{sufijo}@example.com"
    return {
        "organizacion": {
            "nombre": f"Org {sufijo}",
            "slug": slug,
            "email_contacto": f"contacto-{sufijo}@example.com",
        },
        "owner": {
            "nombre": f"Owner {sufijo}",
            "email": email,
            "password": "Password123!",
        },
    }


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _token(usuario: Usuario) -> str:
    payload = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return crear_token(payload)


def _headers(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(usuario)}"}


def test_registro_onboarding_exitoso_crea_tenant_owner_y_wallet(
    client: TestClient,
    db_session: Session,
) -> None:
    payload = _payload()

    response = client.post("/onboarding/registro-organizacion", json=payload)

    assert response.status_code == 201, response.text
    data = _data(response)
    assert data["organizacion"]["slug"] == payload["organizacion"]["slug"]
    assert data["organizacion"]["estado"] == "activa"
    assert data["owner"]["email"] == payload["owner"]["email"]
    assert data["owner"]["rol"] == "owner"
    assert "password" not in data["owner"]
    assert data["wallet_principal"]["saldo"] == "0.00"
    assert data["wallet_principal"]["es_principal"] is True

    organizacion = db_session.get(Organizacion, data["organizacion"]["id"])
    owner = db_session.get(Usuario, data["owner"]["id"])
    wallet = db_session.get(Cuenta, data["wallet_principal"]["id"])
    assert organizacion is not None
    assert owner is not None
    assert wallet is not None
    assert owner.rol == RolUsuario.owner
    assert owner.organizacion_id == organizacion.id
    assert wallet.organizacion_id == organizacion.id
    assert wallet.usuario_id == owner.id


def test_onboarding_endpoint_es_publico(client: TestClient) -> None:
    response = client.post("/onboarding/registro-organizacion", json=_payload())

    assert response.status_code == 201, response.text


def test_onboarding_no_permite_slug_duplicado(client: TestClient) -> None:
    slug = f"duplicado-{uuid4().hex[:8]}"
    primera = client.post("/onboarding/registro-organizacion", json=_payload(slug=slug))
    segunda = client.post("/onboarding/registro-organizacion", json=_payload(slug=slug))

    assert primera.status_code == 201, primera.text
    assert segunda.status_code == 400
    assert "slug" in segunda.json()["detail"].lower()


def test_onboarding_no_permite_email_owner_duplicado(client: TestClient) -> None:
    email = f"owner-duplicado-{uuid4().hex[:8]}@example.com"
    primera = client.post("/onboarding/registro-organizacion", json=_payload(email=email))
    segunda = client.post("/onboarding/registro-organizacion", json=_payload(email=email))

    assert primera.status_code == 201, primera.text
    assert segunda.status_code == 400
    assert "email" in segunda.json()["detail"].lower()


def test_si_falla_owner_no_queda_organizacion_huerfana(
    client: TestClient,
    db_session: Session,
) -> None:
    email = f"owner-rollback-{uuid4().hex[:8]}@example.com"
    slug_fallido = f"rollback-{uuid4().hex[:8]}"
    primera = client.post("/onboarding/registro-organizacion", json=_payload(email=email))
    assert primera.status_code == 201, primera.text

    fallida = client.post(
        "/onboarding/registro-organizacion",
        json=_payload(slug=slug_fallido, email=email),
    )

    assert fallida.status_code == 400
    assert db_session.query(Organizacion).filter(Organizacion.slug == slug_fallido).first() is None


def test_owner_puede_acceder_a_recursos_de_su_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    creado = client.post("/onboarding/registro-organizacion", json=_payload())
    data = _data(creado)
    owner = db_session.get(Usuario, data["owner"]["id"])
    wallet_id = data["wallet_principal"]["id"]
    assert owner is not None
    headers = _headers(owner)

    wallets = client.get("/wallets", headers=headers)
    nueva_wallet = client.post(
        "/wallets",
        headers=headers,
        json={"alias": "Operativa", "tipo": "empresa", "moneda": "ARS", "usuario_id": owner.id},
    )
    movimientos = client.get("/movimientos", headers=headers)
    usuarios = client.get("/admin/usuarios?limit=100", headers=headers)
    reporte = client.get("/admin/reportes/cuentas/estado", headers=headers)
    congelar = client.put(
        f"/admin/cuentas/{wallet_id}/estado",
        headers=headers,
        json={"nuevo_estado": "congelada"},
    )

    assert wallets.status_code == 200, wallets.text
    assert any(wallet["id"] == wallet_id for wallet in _data(wallets))
    assert nueva_wallet.status_code == 201, nueva_wallet.text
    assert _data(nueva_wallet)["usuario_id"] == owner.id
    assert movimientos.status_code == 200, movimientos.text
    assert usuarios.status_code == 200, usuarios.text
    assert reporte.status_code == 200, reporte.text
    assert any(usuario["id"] == owner.id for usuario in usuarios.json())
    assert congelar.status_code == 200, congelar.text
    assert congelar.json()["estado"] == EstadoCuenta.congelada.value


def test_owner_no_accede_a_recursos_de_otra_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    creado_a = client.post("/onboarding/registro-organizacion", json=_payload())
    creado_b = client.post("/onboarding/registro-organizacion", json=_payload())
    data_a = _data(creado_a)
    data_b = _data(creado_b)
    owner_a = db_session.get(Usuario, data_a["owner"]["id"])
    assert owner_a is not None
    headers = _headers(owner_a)

    wallet_ajena = client.get(f"/wallets/{data_b['wallet_principal']['id']}", headers=headers)
    organizaciones = client.get("/organizaciones", headers=headers)

    assert wallet_ajena.status_code == 404
    assert organizaciones.status_code == 403
