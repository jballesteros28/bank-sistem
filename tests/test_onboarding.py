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

    organizacion = db_session.get(Organizacion, UUID(data["organizacion"]["id"]))
    assert organizacion is not None
    assert organizacion.plan_id is not None
    assert organizacion.nombre_comercial == payload["organizacion"]["nombre"]
    assert organizacion.moneda_default == "ARS"
    assert organizacion.timezone == "America/Argentina/Buenos_Aires"
    assert db_session.get(Plan, organizacion.plan_id).codigo == "free"
    assert db_session.get(Usuario, data["owner"]["id"]) is not None
    assert db_session.get(Wallet, data["wallet_principal"]["id"]) is not None
