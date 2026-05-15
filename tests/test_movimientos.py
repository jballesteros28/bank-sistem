from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.notificaciones.models import Notificacion
from app.shared.enums import CanalNotificacion, MonedaWallet, RolUsuario, TipoNotificacion, TipoWallet
from tests.conftest import api_data, auth_headers, create_org, create_org_wallet, create_user, create_wallet


def _balance(client: TestClient, headers: dict[str, str], wallet_id: UUID) -> Decimal:
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
        json={"wallet_destino_id": str(origen.id), "monto": "100.00"},
    )
    assert deposito.status_code == 201, deposito.text
    assert _balance(client, emisor_headers, origen.id) == Decimal("100.00")

    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=emisor_headers,
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "30.00"},
    )
    assert transferencia.status_code == 201, transferencia.text
    movimiento_id = api_data(transferencia)["id"]
    assert _balance(client, emisor_headers, origen.id) == Decimal("70.00")

    retiro = client.post(
        "/api/v1/movimientos/retiro",
        headers=emisor_headers,
        json={"wallet_origen_id": str(origen.id), "monto": "20.00"},
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
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "5.00"},
    )

    assert response.status_code == 403


def test_soporte_no_puede_crear_deposito(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(soporte),
        json={"wallet_destino_id": str(wallet.id), "monto": "10.00"},
    )

    assert response.status_code == 403


def test_soporte_no_puede_crear_retiro(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    wallet = create_wallet(db_session, soporte, saldo=Decimal("10.00"))

    response = client.post(
        "/api/v1/movimientos/retiro",
        headers=auth_headers(soporte),
        json={"wallet_origen_id": str(wallet.id), "monto": "5.00"},
    )

    assert response.status_code == 403


def test_soporte_no_puede_crear_cashback(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/cashback",
        headers=auth_headers(soporte),
        json={"wallet_destino_id": str(wallet.id), "monto": "3.00"},
    )

    assert response.status_code == 403


def test_soporte_no_puede_crear_ajuste_admin(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/ajuste-admin",
        headers=auth_headers(soporte),
        json={
            "wallet_destino_id": str(wallet.id),
            "monto": "7.00",
            "operacion": "credito",
            "motivo": "control operativo",
        },
    )

    assert response.status_code == 403


def test_soporte_puede_consultar_movimientos_de_su_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    created = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "11.00"},
    )
    assert created.status_code == 201, created.text

    listed = client.get("/api/v1/movimientos", headers=auth_headers(soporte))

    assert listed.status_code == 200, listed.text
    assert [movimiento["tipo"] for movimiento in api_data(listed)] == ["deposito"]


def test_cliente_puede_pagar_a_wallet_de_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    cliente = create_user(db_session, org)
    origen = create_wallet(db_session, cliente, saldo=Decimal("100.00"))
    destino = create_org_wallet(db_session, org, es_principal=True)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(cliente),
        json={
            "wallet_origen_id": str(origen.id),
            "wallet_destino_id": str(destino.id),
            "monto": "25.00",
            "descripcion": "Compra interna",
        },
    )

    assert response.status_code == 201, response.text
    assert api_data(response)["tipo"] == "pago"
    db_session.expire_all()
    assert db_session.get(type(origen), origen.id).saldo == Decimal("75.00")
    assert db_session.get(type(destino), destino.id).saldo == Decimal("25.00")
    payer_notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.tipo == TipoNotificacion.pago_organizacion_realizado,
            Notificacion.canal == CanalNotificacion.interna,
            Notificacion.usuario_id == cliente.id,
        )
    )
    owner_notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.tipo == TipoNotificacion.pago_organizacion_recibido,
            Notificacion.canal == CanalNotificacion.interna,
            Notificacion.usuario_id == owner.id,
        )
    )
    audit_log = db_session.scalar(select(AuditLog).where(AuditLog.evento == "pago_organizacion_realizado"))
    assert payer_notification is not None
    assert owner_notification is not None
    assert audit_log is not None


def test_pago_organizacion_falla_si_no_hay_saldo(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    cliente = create_user(db_session, org)
    origen = create_wallet(db_session, cliente, saldo=Decimal("5.00"))
    destino = create_org_wallet(db_session, org)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Saldo insuficiente."


def test_pago_organizacion_falla_entre_organizaciones_distintas(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    cliente = create_user(db_session, org_a)
    origen = create_wallet(db_session, cliente, saldo=Decimal("50.00"))
    destino = create_org_wallet(db_session, org_b)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 403


def test_pago_organizacion_falla_si_las_monedas_son_distintas(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    cliente = create_user(db_session, org)
    origen = create_wallet(db_session, cliente, saldo=Decimal("50.00"), moneda=MonedaWallet.ARS)
    destino = create_org_wallet(db_session, org, moneda=MonedaWallet.USD)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede operar entre monedas distintas."


def test_pago_organizacion_falla_si_destino_no_es_wallet_de_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    cliente = create_user(db_session, org)
    receptor = create_user(db_session, org)
    origen = create_wallet(db_session, cliente, saldo=Decimal("50.00"))
    destino = create_wallet(db_session, receptor)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La wallet destino debe ser de organizacion."


def test_pago_organizacion_falla_si_origen_no_es_wallet_de_usuario(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    origen = create_org_wallet(db_session, org, saldo=Decimal("50.00"), tipo=TipoWallet.operativa)
    destino = create_org_wallet(db_session, org)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(admin),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La wallet origen debe ser de usuario."


def test_soporte_no_puede_crear_pago_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    origen = create_wallet(db_session, soporte, saldo=Decimal("50.00"))
    destino = create_org_wallet(db_session, org)

    response = client.post(
        "/api/v1/movimientos/pago-organizacion",
        headers=auth_headers(soporte),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert response.status_code == 403
