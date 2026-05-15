from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet


def _balance(client: TestClient, headers: dict[str, str], wallet_id: int) -> Decimal:
    response = client.get(f"/api/v1/wallets/{wallet_id}/balance", headers=headers)
    assert response.status_code == 200, response.text
    return Decimal(api_data(response)["saldo"])


def test_deposito_admin_transferencia_retiro_y_reversa(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    emisor = create_user(db_session, org)
    receptor = create_user(db_session, org)
    origen = create_wallet(db_session, emisor)
    destino = create_wallet(db_session, receptor)
    admin_headers = auth_headers(admin)
    emisor_headers = auth_headers(emisor)

    deposito = client.post(
        "/api/v1/movimientos/deposito",
        headers=admin_headers,
        json={"wallet_destino_id": origen.id, "monto": "100.00"},
    )
    assert deposito.status_code == 201, deposito.text
    assert _balance(client, emisor_headers, origen.id) == Decimal("100.00")

    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=emisor_headers,
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "30.00"},
    )
    assert transferencia.status_code == 201, transferencia.text
    movimiento_id = api_data(transferencia)["id"]
    assert _balance(client, emisor_headers, origen.id) == Decimal("70.00")

    retiro = client.post(
        "/api/v1/movimientos/retiro",
        headers=emisor_headers,
        json={"wallet_origen_id": origen.id, "monto": "20.00"},
    )
    assert retiro.status_code == 201, retiro.text
    assert _balance(client, emisor_headers, origen.id) == Decimal("50.00")

    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=admin_headers,
        json={"motivo_reversa": "error operativo"},
    )
    assert reversa.status_code == 201, reversa.text
    assert api_data(reversa)["tipo"] == "reversa"
    assert _balance(client, emisor_headers, origen.id) == Decimal("80.00")


def test_bloquea_movimientos_cross_organization(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    user_a = create_user(db_session, org_a)
    user_b = create_user(db_session, org_b)
    origen = create_wallet(db_session, user_a, saldo=Decimal("50.00"))
    destino = create_wallet(db_session, user_b)

    response = client.post(
        "/api/v1/movimientos/transferencia",
        headers=auth_headers(user_a),
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "5.00"},
    )

    assert response.status_code == 403

