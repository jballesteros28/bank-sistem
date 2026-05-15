from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet


def test_crear_y_listar_wallets(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    created = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Operativa", "tipo": "empresa", "moneda": "ARS"},
    )
    assert created.status_code == 201, created.text
    assert api_data(created)["alias"] == "Operativa"

    listed = client.get("/api/v1/wallets", headers=auth_headers(owner))
    assert listed.status_code == 200, listed.text
    assert len(api_data(listed)) == 1


def test_wallets_aisladas_por_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    user_a = create_user(db_session, org_a)
    user_b = create_user(db_session, org_b)
    wallet_b = create_wallet(db_session, user_b, saldo=Decimal("10.00"))

    response = client.get(f"/api/v1/wallets/{wallet_b.id}", headers=auth_headers(user_a))

    assert response.status_code == 404

