from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.movimientos.models import Movimiento
from app.apps.notificaciones.models import Notificacion
from app.apps.wallets.models import Wallet
from app.shared.enums import (
    CanalNotificacion,
    EstadoMovimiento,
    MonedaWallet,
    RolUsuario,
    TipoNotificacion,
    TipoWallet,
)
from tests.conftest import api_data, auth_headers, create_org, create_org_wallet, create_user, create_wallet


def _balance(client: TestClient, headers: dict[str, str], wallet_id: UUID) -> Decimal:
    response = client.get(f"/api/v1/wallets/{wallet_id}/balance", headers=headers)
    assert response.status_code == 200, response.text
    return Decimal(api_data(response)["saldo"])


def _saldo_db(db: Session, wallet_id: UUID) -> Decimal:
    db.expire_all()
    wallet = db.get(Wallet, wallet_id)
    assert wallet is not None
    return wallet.saldo


def test_deposito_crea_movimiento_con_origen_null_y_aumenta_saldo(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "40.00"},
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["wallet_origen_id"] is None
    assert data["wallet_destino_id"] == str(wallet.id)
    assert data["moneda"] == "ARS"
    assert _saldo_db(db_session, wallet.id) == Decimal("40.00")


def test_retiro_crea_movimiento_con_destino_null_y_disminuye_saldo(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente, saldo=Decimal("50.00"))

    response = client.post(
        "/api/v1/movimientos/retiro",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(wallet.id), "monto": "15.00"},
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["wallet_origen_id"] == str(wallet.id)
    assert data["wallet_destino_id"] is None
    assert _saldo_db(db_session, wallet.id) == Decimal("35.00")


def test_cashback_crea_movimiento_con_origen_null_y_aumenta_saldo(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/cashback",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "8.00"},
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["wallet_origen_id"] is None
    assert data["wallet_destino_id"] == str(wallet.id)
    assert _saldo_db(db_session, wallet.id) == Decimal("8.00")


def test_ajuste_admin_credito_y_debito_usan_una_sola_wallet(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente, saldo=Decimal("20.00"))

    credito = client.post(
        "/api/v1/movimientos/ajuste-admin",
        headers=auth_headers(admin),
        json={
            "wallet_id": str(wallet.id),
            "monto": "12.00",
            "operacion": "credito",
            "motivo": "control operativo",
        },
    )
    debito = client.post(
        "/api/v1/movimientos/ajuste-admin",
        headers=auth_headers(admin),
        json={
            "wallet_id": str(wallet.id),
            "monto": "7.00",
            "operacion": "debito",
            "motivo": "control operativo",
        },
    )

    assert credito.status_code == 201, credito.text
    assert debito.status_code == 201, debito.text
    credito_data = api_data(credito)
    debito_data = api_data(debito)
    assert credito_data["wallet_origen_id"] is None
    assert credito_data["wallet_destino_id"] == str(wallet.id)
    assert debito_data["wallet_origen_id"] == str(wallet.id)
    assert debito_data["wallet_destino_id"] is None
    assert _saldo_db(db_session, wallet.id) == Decimal("25.00")


def test_transferencia_y_pago_mueven_saldo_entre_dos_wallets(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    emisor = create_user(db_session, org)
    receptor = create_user(db_session, org)
    origen = create_wallet(db_session, emisor, saldo=Decimal("100.00"))
    destino = create_wallet(db_session, receptor)

    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=auth_headers(emisor),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "30.00"},
    )
    pago = client.post(
        "/api/v1/movimientos/pago",
        headers=auth_headers(emisor),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "10.00"},
    )

    assert transferencia.status_code == 201, transferencia.text
    assert pago.status_code == 201, pago.text
    for response in (transferencia, pago):
        data = api_data(response)
        assert data["wallet_origen_id"] == str(origen.id)
        assert data["wallet_destino_id"] == str(destino.id)
    assert _saldo_db(db_session, origen.id) == Decimal("60.00")
    assert _saldo_db(db_session, destino.id) == Decimal("40.00")


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
    assert api_data(deposito)["wallet_origen_id"] is None
    assert api_data(deposito)["wallet_destino_id"] == str(origen.id)
    assert _balance(client, emisor_headers, origen.id) == Decimal("100.00")

    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=emisor_headers,
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "30.00"},
    )
    assert transferencia.status_code == 201, transferencia.text
    transferencia_data = api_data(transferencia)
    movimiento_id = transferencia_data["id"]
    assert transferencia_data["wallet_origen_id"] == str(origen.id)
    assert transferencia_data["wallet_destino_id"] == str(destino.id)
    assert _balance(client, emisor_headers, origen.id) == Decimal("70.00")

    retiro = client.post(
        "/api/v1/movimientos/retiro",
        headers=emisor_headers,
        json={"wallet_origen_id": str(origen.id), "monto": "20.00"},
    )
    assert retiro.status_code == 201, retiro.text
    assert api_data(retiro)["wallet_origen_id"] == str(origen.id)
    assert api_data(retiro)["wallet_destino_id"] is None
    assert _balance(client, emisor_headers, origen.id) == Decimal("50.00")

    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=admin_headers,
        json={"motivo_reversa": "error operativo"},
    )
    assert reversa.status_code == 201, reversa.text
    reversa_data = api_data(reversa)
    assert reversa_data["tipo"] == "reversa"
    assert reversa_data["wallet_origen_id"] == str(destino.id)
    assert reversa_data["wallet_destino_id"] == str(origen.id)
    assert _balance(client, emisor_headers, origen.id) == Decimal("80.00")


def test_reversa_de_deposito_debita_wallet_destino_original(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    deposito = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "25.00"},
    )
    movimiento_id = api_data(deposito)["id"]
    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "error operativo"},
    )

    assert reversa.status_code == 201, reversa.text
    data = api_data(reversa)
    assert data["wallet_origen_id"] == str(wallet.id)
    assert data["wallet_destino_id"] is None
    assert data["movimiento_origen_id"] == movimiento_id
    assert data["motivo_reversa"] == "error operativo"
    assert _saldo_db(db_session, wallet.id) == Decimal("0.00")
    original = db_session.get(Movimiento, UUID(movimiento_id))
    assert original is not None
    assert original.estado == EstadoMovimiento.revertida


def test_reversa_de_retiro_acredita_wallet_origen_original(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente, saldo=Decimal("40.00"))

    retiro = client.post(
        "/api/v1/movimientos/retiro",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(wallet.id), "monto": "10.00"},
    )
    movimiento_id = api_data(retiro)["id"]
    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "error operativo"},
    )

    assert reversa.status_code == 201, reversa.text
    data = api_data(reversa)
    assert data["wallet_origen_id"] is None
    assert data["wallet_destino_id"] == str(wallet.id)
    assert _saldo_db(db_session, wallet.id) == Decimal("40.00")


def test_reversa_de_transferencia_invierte_origen_y_destino(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    emisor = create_user(db_session, org)
    receptor = create_user(db_session, org)
    origen = create_wallet(db_session, emisor, saldo=Decimal("60.00"))
    destino = create_wallet(db_session, receptor)

    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=auth_headers(emisor),
        json={"wallet_origen_id": str(origen.id), "wallet_destino_id": str(destino.id), "monto": "20.00"},
    )
    movimiento_id = api_data(transferencia)["id"]
    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "error operativo"},
    )

    assert reversa.status_code == 201, reversa.text
    data = api_data(reversa)
    assert data["wallet_origen_id"] == str(destino.id)
    assert data["wallet_destino_id"] == str(origen.id)
    assert _saldo_db(db_session, origen.id) == Decimal("60.00")
    assert _saldo_db(db_session, destino.id) == Decimal("0.00")


def test_reversa_falla_si_debe_debitar_y_no_hay_saldo(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    receptor = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)
    destino = create_wallet(db_session, receptor)

    deposito = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "30.00"},
    )
    movimiento_id = api_data(deposito)["id"]
    transferencia = client.post(
        "/api/v1/movimientos/transferencia",
        headers=auth_headers(cliente),
        json={"wallet_origen_id": str(wallet.id), "wallet_destino_id": str(destino.id), "monto": "30.00"},
    )
    assert transferencia.status_code == 201, transferencia.text

    reversa = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "sin saldo para reversa"},
    )

    assert reversa.status_code == 400
    assert reversa.json()["detail"] == "Saldo insuficiente."


def test_no_permite_doble_reversa(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    deposito = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "10.00"},
    )
    movimiento_id = api_data(deposito)["id"]
    primera = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "error operativo"},
    )
    segunda = client.post(
        f"/api/v1/movimientos/{movimiento_id}/reversa",
        headers=auth_headers(admin),
        json={"motivo_reversa": "segundo intento"},
    )

    assert primera.status_code == 201, primera.text
    assert segunda.status_code == 400
    assert segunda.json()["detail"] == "El movimiento ya fue revertido."


def test_consistencia_bloquea_payloads_invalidos_y_misma_wallet(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente, saldo=Decimal("10.00"))
    headers = auth_headers(admin)

    deposito_sin_destino = client.post("/api/v1/movimientos/deposito", headers=headers, json={"monto": "1.00"})
    retiro_sin_origen = client.post("/api/v1/movimientos/retiro", headers=headers, json={"monto": "1.00"})
    transferencia_sin_destino = client.post(
        "/api/v1/movimientos/transferencia",
        headers=headers,
        json={"wallet_origen_id": str(wallet.id), "monto": "1.00"},
    )
    misma_wallet = client.post(
        "/api/v1/movimientos/transferencia",
        headers=headers,
        json={"wallet_origen_id": str(wallet.id), "wallet_destino_id": str(wallet.id), "monto": "1.00"},
    )

    assert deposito_sin_destino.status_code == 422
    assert retiro_sin_origen.status_code == 422
    assert transferencia_sin_destino.status_code == 422
    assert misma_wallet.status_code == 400
    assert misma_wallet.json()["detail"] == "No se puede operar sobre la misma wallet."


def test_auditoria_de_movimiento_registra_wallets_existentes_monto_y_moneda(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "11.00"},
    )

    assert response.status_code == 201, response.text
    audit_log = db_session.scalar(select(AuditLog).where(AuditLog.evento == "movimiento_registrado"))
    assert audit_log is not None
    assert audit_log.actor_tipo == "usuario"
    assert audit_log.actor_usuario_id == admin.id
    assert audit_log.actor_api_key_id is None
    assert audit_log.metadata_log["tipo_operacion"] == "deposito"
    assert audit_log.metadata_log["monto"] == "11.00"
    assert audit_log.metadata_log["moneda"] == "ARS"
    assert "wallet_origen_id" not in audit_log.metadata_log
    assert audit_log.metadata_log["wallet_destino_id"] == str(wallet.id)


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
            "wallet_id": str(wallet.id),
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
    data = api_data(response)
    assert data["tipo"] == "pago"
    assert data["wallet_origen_id"] == str(origen.id)
    assert data["wallet_destino_id"] == str(destino.id)
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
    assert audit_log.metadata_log["wallet_origen_id"] == str(origen.id)
    assert audit_log.metadata_log["wallet_destino_id"] == str(destino.id)
    assert audit_log.metadata_log["moneda"] == "ARS"


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
