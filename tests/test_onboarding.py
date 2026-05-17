from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID

from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from tests.conftest import api_data, onboarding_payload


def test_onboarding_crea_organizacion_owner_y_wallet_principal(
    client: TestClient,
    db_session: Session,
) -> None:
    payload = onboarding_payload()

    response = client.post("/api/v1/onboarding/registro-organizacion", json=payload)

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["organizacion"]["slug"] == payload["organizacion"]["slug"]
    assert data["owner"]["rol"] == "owner"
    assert data["wallet_principal"]["es_principal"] is True
    assert data["wallet_principal"]["saldo"] == "0.00"
    assert data["wallet_principal"]["owner_type"] == "usuario"
    assert data["wallet_principal"]["usuario_id"] == data["owner"]["id"]
    assert data["wallet_principal"]["organizacion_owner_id"] is None
    assert data["wallet_organizacion_principal"]["es_principal"] is True
    assert data["wallet_organizacion_principal"]["owner_type"] == "organizacion"
    assert data["wallet_organizacion_principal"]["usuario_id"] is None
    assert data["wallet_organizacion_principal"]["organizacion_owner_id"] == data["organizacion"]["id"]

    organizacion = db_session.get(Organizacion, UUID(data["organizacion"]["id"]))
    assert organizacion is not None
    assert organizacion.plan_id is not None
    assert organizacion.nombre_comercial == payload["organizacion"]["nombre"]
    assert organizacion.moneda_default == "ARS"
    assert organizacion.timezone == "America/Argentina/Buenos_Aires"
    assert db_session.get(Plan, organizacion.plan_id).codigo == "free"
    assert db_session.get(Usuario, UUID(data["owner"]["id"])) is not None
    assert db_session.get(Wallet, UUID(data["wallet_principal"]["id"])) is not None
    assert db_session.get(Wallet, UUID(data["wallet_organizacion_principal"]["id"])) is not None


def test_onboarding_devuelve_error_claro_para_slug_duplicado(client: TestClient) -> None:
    payload = onboarding_payload(slug="tenant-duplicado")
    creado = client.post("/api/v1/onboarding/registro-organizacion", json=payload)
    assert creado.status_code == 201, creado.text

    repetido = client.post("/api/v1/onboarding/registro-organizacion", json=payload)

    assert repetido.status_code == 400
    assert repetido.json() == {
        "success": False,
        "error": "HTTPException",
        "detail": "Ya existe una organizacion con ese slug.",
    }


def test_onboarding_devuelve_error_claro_para_email_duplicado(client: TestClient) -> None:
    payload = onboarding_payload(email="owner-duplicado@example.com")
    creado = client.post("/api/v1/onboarding/registro-organizacion", json=payload)
    assert creado.status_code == 201, creado.text

    repetido_email = onboarding_payload(slug="tenant-email-duplicado", email=payload["owner"]["email"])
    repetido = client.post("/api/v1/onboarding/registro-organizacion", json=repetido_email)

    assert repetido.status_code == 400
    assert repetido.json() == {
        "success": False,
        "error": "HTTPException",
        "detail": "Ya existe un usuario con ese email.",
    }
