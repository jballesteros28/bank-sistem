from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.integraciones.models import WebhookDelivery, WebhookEndpoint
from app.apps.integraciones.services import encrypt_webhook_secret
from app.apps.movimientos.models import Movimiento
from app.apps.notificaciones.models import Notificacion
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.wallets.models import Wallet
from app.shared.enums import (
    CanalNotificacion,
    EstadoReglaRecompensa,
    MonedaWallet,
    RolUsuario,
    TipoMovimiento,
    TipoNotificacion,
)
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet


def _rule_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "nombre": "Cashback 10%",
        "tipo": "cashback",
        "porcentaje_cashback": "10.00",
        "moneda_recompensa": "ARS",
        "monto_minimo_compra": "1000.00",
        "monto_maximo_recompensa": "2000.00",
    }
    payload.update(overrides)
    return payload


def _create_rule(client: TestClient, headers: dict[str, str], **overrides: object) -> dict[str, object]:
    response = client.post("/api/v1/recompensas/reglas", headers=headers, json=_rule_payload(**overrides))
    assert response.status_code == 201, response.text
    return api_data(response)


def _saldo_db(db: Session, wallet_id) -> Decimal:
    db.expire_all()
    wallet = db.get(Wallet, wallet_id)
    assert wallet is not None
    return wallet.saldo


def test_owner_crea_regla_y_soporte_cliente_no_crean(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)

    created = client.post("/api/v1/recompensas/reglas", headers=auth_headers(owner), json=_rule_payload())
    soporte_response = client.post("/api/v1/recompensas/reglas", headers=auth_headers(soporte), json=_rule_payload())
    cliente_response = client.post("/api/v1/recompensas/reglas", headers=auth_headers(cliente), json=_rule_payload())

    assert created.status_code == 201, created.text
    data = api_data(created)
    assert data["tipo"] == "cashback"
    assert data["estado"] == "activa"
    assert data["organizacion_id"] == str(org.id)
    assert soporte_response.status_code == 403
    assert cliente_response.status_code == 403


def test_listar_reglas_respeta_organizacion_y_soporte_puede_ver(
    client: TestClient,
    db_session: Session,
) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    admin_a = create_user(db_session, org_a, RolUsuario.admin)
    soporte_a = create_user(db_session, org_a, RolUsuario.soporte)
    admin_b = create_user(db_session, org_b, RolUsuario.admin)

    rule_a = _create_rule(client, auth_headers(admin_a), nombre="Cashback Org A")
    _create_rule(client, auth_headers(admin_b), nombre="Cashback Org B")

    admin_list = client.get("/api/v1/recompensas/reglas", headers=auth_headers(admin_a))
    soporte_list = client.get("/api/v1/recompensas/reglas", headers=auth_headers(soporte_a))

    assert admin_list.status_code == 200, admin_list.text
    assert soporte_list.status_code == 200, soporte_list.text
    assert [item["id"] for item in api_data(admin_list)] == [rule_a["id"]]
    assert [item["id"] for item in api_data(soporte_list)] == [rule_a["id"]]


def test_validaciones_de_regla_recompensa(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    headers = auth_headers(owner)

    invalid_percentage = client.post(
        "/api/v1/recompensas/reglas",
        headers=headers,
        json=_rule_payload(porcentaje_cashback="101.00"),
    )
    invalid_fixed = client.post(
        "/api/v1/recompensas/reglas",
        headers=headers,
        json=_rule_payload(porcentaje_cashback=None, monto_fijo="0.00"),
    )
    missing_reward = client.post(
        "/api/v1/recompensas/reglas",
        headers=headers,
        json=_rule_payload(porcentaje_cashback=None, monto_fijo=None),
    )
    invalid_dates = client.post(
        "/api/v1/recompensas/reglas",
        headers=headers,
        json=_rule_payload(fecha_inicio="2026-05-20T00:00:00Z", fecha_fin="2026-05-19T00:00:00Z"),
    )

    assert invalid_percentage.status_code == 422
    assert invalid_fixed.status_code == 422
    assert missing_reward.status_code == 422
    assert invalid_dates.status_code == 422


def test_simulacion_calcula_cashback_minimo_maximo_inactiva_y_sin_regla(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    org_sin_reglas = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    admin_sin_reglas = create_user(db_session, org_sin_reglas, RolUsuario.admin)
    rule = _create_rule(client, auth_headers(admin))

    ok_response = client.post(
        "/api/v1/recompensas/simular",
        headers=auth_headers(soporte),
        json={"monto_compra": "15000.00", "regla_id": rule["id"]},
    )
    below_minimum = client.post(
        "/api/v1/recompensas/simular",
        headers=auth_headers(soporte),
        json={"monto_compra": "500.00", "regla_id": rule["id"]},
    )
    capped = client.post(
        "/api/v1/recompensas/simular",
        headers=auth_headers(soporte),
        json={"monto_compra": "30000.00", "regla_id": rule["id"]},
    )
    no_rule = client.post(
        "/api/v1/recompensas/simular",
        headers=auth_headers(admin_sin_reglas),
        json={"monto_compra": "30000.00"},
    )
    inactive_patch = client.patch(
        f"/api/v1/recompensas/reglas/{rule['id']}",
        headers=auth_headers(admin),
        json={"estado": "inactiva"},
    )
    inactive = client.post(
        "/api/v1/recompensas/simular",
        headers=auth_headers(soporte),
        json={"monto_compra": "15000.00", "regla_id": rule["id"]},
    )

    assert ok_response.status_code == 200, ok_response.text
    assert api_data(ok_response)["aplica"] is True
    assert Decimal(api_data(ok_response)["monto_recompensa"]) == Decimal("1500.00")
    assert below_minimum.status_code == 200
    assert api_data(below_minimum)["aplica"] is False
    assert capped.status_code == 200
    assert Decimal(api_data(capped)["monto_recompensa"]) == Decimal("2000.00")
    assert no_rule.status_code == 200
    assert api_data(no_rule)["aplica"] is False
    assert inactive_patch.status_code == 200, inactive_patch.text
    assert inactive.status_code == 200
    assert api_data(inactive)["aplica"] is False


def test_aplicar_recompensa_acredita_wallet_y_crea_movimiento_aplicacion_notificacion_audit_y_webhook(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.enviar_webhook_delivery", lambda delivery_id: None)
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)
    rule = _create_rule(client, auth_headers(admin))
    webhook = WebhookEndpoint(
        organizacion_id=org.id,
        nombre="Rewards",
        url="https://example.com/rewards",
        eventos=["recompensa.aplicada"],
        secret_encrypted=encrypt_webhook_secret("secret-rewards-123"),
        activo=True,
    )
    db_session.add(webhook)
    db_session.commit()

    response = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet.id),
            "monto_compra": "15000.00",
            "regla_id": rule["id"],
            "referencia_externa": "compra-externa-1",
            "metadata": {"ticket": "A-100"},
        },
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert Decimal(data["aplicacion"]["monto_recompensa"]) == Decimal("1500.00")
    assert data["movimiento"]["tipo"] == "cashback"
    assert data["movimiento"]["wallet_destino_id"] == str(wallet.id)
    assert _saldo_db(db_session, wallet.id) == Decimal("1500.00")

    movimiento = db_session.get(Movimiento, UUID(data["movimiento"]["id"]))
    aplicacion = db_session.get(AplicacionRecompensa, UUID(data["aplicacion"]["id"]))
    notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.tipo == TipoNotificacion.recompensa_aplicada,
            Notificacion.canal == CanalNotificacion.interna,
            Notificacion.usuario_id == cliente.id,
        )
    )
    audit_log = db_session.scalar(select(AuditLog).where(AuditLog.evento == "recompensa_aplicada"))
    delivery = db_session.scalar(select(WebhookDelivery).where(WebhookDelivery.evento == "recompensa.aplicada"))

    assert movimiento is not None
    assert movimiento.tipo == TipoMovimiento.cashback
    assert aplicacion is not None
    assert aplicacion.referencia_externa == "compra-externa-1"
    assert notification is not None
    assert audit_log is not None
    assert audit_log.metadata_log["aplicacion_id"] == str(aplicacion.id)
    assert delivery is not None
    assert delivery.payload["data"]["aplicacion"]["id"] == str(aplicacion.id)


def test_aplicar_recompensa_evita_duplicado_por_referencia(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)
    rule = _create_rule(client, auth_headers(admin))
    payload = {
        "usuario_id": str(cliente.id),
        "wallet_destino_id": str(wallet.id),
        "monto_compra": "15000.00",
        "regla_id": rule["id"],
        "referencia_externa": "compra-duplicada",
    }

    first = client.post("/api/v1/recompensas/aplicar", headers=auth_headers(admin), json=payload)
    second = client.post("/api/v1/recompensas/aplicar", headers=auth_headers(admin), json=payload)

    assert first.status_code == 201, first.text
    assert second.status_code == 400
    assert second.json()["detail"] == "Ya existe una recompensa aplicada con esa referencia externa."


def test_aplicar_credito_tienda_puntos_crea_movimiento_credito_tienda(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente, moneda=MonedaWallet.PUNTOS)
    rule = _create_rule(
        client,
        auth_headers(admin),
        nombre="Puntos fijos",
        tipo="puntos",
        porcentaje_cashback=None,
        monto_fijo="25.00",
        moneda_recompensa="PUNTOS",
        monto_minimo_compra=None,
        monto_maximo_recompensa=None,
    )

    response = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet.id),
            "monto_compra": "3000.00",
            "regla_id": rule["id"],
        },
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["movimiento"]["tipo"] == "credito_tienda"
    assert data["movimiento"]["moneda"] == "PUNTOS"
    assert Decimal(data["aplicacion"]["monto_recompensa"]) == Decimal("25.00")
    assert _saldo_db(db_session, wallet.id) == Decimal("25.00")


def test_aplicar_recompensa_valida_wallet_usuario_organizacion_y_moneda(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    other_org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    otro_cliente = create_user(db_session, org)
    cliente_externo = create_user(db_session, other_org)
    wallet_otro_usuario = create_wallet(db_session, otro_cliente)
    wallet_otra_org = create_wallet(db_session, cliente_externo)
    wallet_usd = create_wallet(db_session, cliente, moneda=MonedaWallet.USD)
    rule = _create_rule(client, auth_headers(admin))

    wrong_user_wallet = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet_otro_usuario.id),
            "monto_compra": "15000.00",
            "regla_id": rule["id"],
        },
    )
    cross_org = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet_otra_org.id),
            "monto_compra": "15000.00",
            "regla_id": rule["id"],
        },
    )
    wrong_currency = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet_usd.id),
            "monto_compra": "15000.00",
            "regla_id": rule["id"],
        },
    )

    assert wrong_user_wallet.status_code == 400
    assert wrong_user_wallet.json()["detail"] == "La wallet destino no pertenece al usuario."
    assert cross_org.status_code == 403
    assert wrong_currency.status_code == 400
    assert wrong_currency.json()["detail"] == "La moneda de la wallet destino no coincide con la recompensa."


def test_soporte_y_cliente_no_pueden_aplicar_recompensas(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)
    rule = _create_rule(client, auth_headers(admin))
    payload = {
        "usuario_id": str(cliente.id),
        "wallet_destino_id": str(wallet.id),
        "monto_compra": "15000.00",
        "regla_id": rule["id"],
    }

    soporte_response = client.post("/api/v1/recompensas/aplicar", headers=auth_headers(soporte), json=payload)
    cliente_response = client.post("/api/v1/recompensas/aplicar", headers=auth_headers(cliente), json=payload)

    assert soporte_response.status_code == 403
    assert cliente_response.status_code == 403


def test_cliente_puede_ver_sus_aplicaciones(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)
    rule = _create_rule(client, auth_headers(admin))
    applied = client.post(
        "/api/v1/recompensas/aplicar",
        headers=auth_headers(admin),
        json={
            "usuario_id": str(cliente.id),
            "wallet_destino_id": str(wallet.id),
            "monto_compra": "15000.00",
            "regla_id": rule["id"],
        },
    )
    assert applied.status_code == 201, applied.text

    mine = client.get("/api/v1/recompensas/aplicaciones/me", headers=auth_headers(cliente))
    admin_list = client.get("/api/v1/recompensas/aplicaciones", headers=auth_headers(admin))

    assert mine.status_code == 200, mine.text
    assert [item["id"] for item in api_data(mine)] == [api_data(applied)["aplicacion"]["id"]]
    assert admin_list.status_code == 200, admin_list.text
    assert [item["id"] for item in api_data(admin_list)] == [api_data(applied)["aplicacion"]["id"]]
