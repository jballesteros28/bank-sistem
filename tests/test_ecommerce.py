from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.ecommerce.models import EcommerceOrderEvent
from app.apps.integraciones.models import APIKey, WebhookDelivery, WebhookEndpoint
from app.apps.integraciones.services import encrypt_webhook_secret
from app.apps.movimientos.models import Movimiento
from app.apps.notificaciones.models import Notificacion
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.shared.enums import (
    CanalNotificacion,
    EstadoReglaRecompensa,
    MonedaRecompensa,
    MonedaWallet,
    RolUsuario,
    TipoMovimiento,
    TipoNotificacion,
    TipoRecompensa,
)
from tests.conftest import api_data, auth_headers, create_org, create_user


def _create_api_key(client: TestClient, user: Usuario, scopes: list[str]) -> str:
    response = client.post(
        "/api/v1/integraciones/api-keys",
        headers=auth_headers(user),
        json={"nombre": "Ecommerce", "scopes": scopes},
    )
    assert response.status_code == 201, response.text
    return str(api_data(response)["api_key"])


def _store_rule(db: Session, org, **overrides: object) -> ReglaRecompensa:
    data = {
        "organizacion_id": org.id,
        "nombre": "Cashback ecommerce 10%",
        "descripcion": "Regla ecommerce test",
        "tipo": TipoRecompensa.cashback,
        "estado": EstadoReglaRecompensa.activa,
        "porcentaje_cashback": Decimal("10.00"),
        "monto_fijo": None,
        "moneda_recompensa": MonedaRecompensa.ARS,
        "monto_minimo_compra": Decimal("1000.00"),
        "monto_maximo_recompensa": Decimal("2000.00"),
        "acumulable": True,
    }
    data.update(overrides)
    rule = ReglaRecompensa(**data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def _order_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "proveedor": "generic",
        "external_order_id": "order-1001",
        "customer_email": "comprador@example.com",
        "customer_name": "Comprador Ecommerce",
        "amount": "20000.00",
        "currency": "ARS",
        "metadata": {"source": "pytest"},
    }
    payload.update(overrides)
    return payload


def test_order_paid_requiere_api_key_y_scope_ecommerce_write(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    raw_key = _create_api_key(client, owner, ["movimientos:write"])

    no_key = client.post("/api/v1/ext/ecommerce/order-paid", json=_order_payload())
    wrong_scope = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(),
    )

    assert no_key.status_code == 401
    assert wrong_scope.status_code == 403
    assert wrong_scope.json()["detail"] == "Scope requerido: ecommerce:write."


def test_order_paid_aplica_recompensa_crea_cliente_wallet_movimiento_notificacion_audit_y_webhooks(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.enviar_webhook_delivery", lambda delivery_id: None)
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _store_rule(db_session, org)
    raw_key = _create_api_key(client, owner, ["ecommerce:write", "ecommerce:read"])
    webhook = WebhookEndpoint(
        organizacion_id=org.id,
        nombre="Ecommerce hook",
        url="https://example.com/ecommerce",
        eventos=["ecommerce.order_paid", "ecommerce.order_processed", "recompensa.aplicada"],
        secret_encrypted=encrypt_webhook_secret("secret-ecommerce-123"),
        activo=True,
    )
    db_session.add(webhook)
    db_session.commit()

    response = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(),
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["event"]["procesado"] is True
    assert data["event"]["error_procesamiento"] is None
    assert Decimal(data["recompensa_aplicada"]["monto_recompensa"]) == Decimal("2000.00")
    assert data["movimiento"]["tipo"] == "cashback"

    db_session.expire_all()
    api_key = db_session.scalar(select(APIKey).where(APIKey.key_prefix == raw_key[:20]))
    usuario = db_session.scalar(select(Usuario).where(Usuario.email == "comprador@example.com"))
    assert api_key is not None
    assert usuario is not None
    assert usuario.organizacion_id == org.id
    assert usuario.rol == RolUsuario.cliente

    wallet = db_session.scalar(select(Wallet).where(Wallet.usuario_id == usuario.id, Wallet.es_principal.is_(True)))
    assert wallet is not None
    assert wallet.moneda == MonedaWallet.ARS
    assert wallet.saldo == Decimal("2000.00")

    event = db_session.get(EcommerceOrderEvent, UUID(data["event"]["id"]))
    aplicacion = db_session.get(AplicacionRecompensa, UUID(data["recompensa_aplicada"]["id"]))
    movimiento = db_session.get(Movimiento, UUID(data["movimiento"]["id"]))
    notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.usuario_id == usuario.id,
            Notificacion.tipo == TipoNotificacion.recompensa_aplicada,
            Notificacion.canal == CanalNotificacion.interna,
        )
    )
    processed_audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "ecommerce.order_paid_procesado"))
    deliveries = db_session.scalars(select(WebhookDelivery).where(WebhookDelivery.organizacion_id == org.id)).all()

    assert event is not None
    assert event.recompensa_aplicada_id == aplicacion.id
    assert aplicacion is not None
    assert aplicacion.movimiento_id == movimiento.id
    assert movimiento is not None
    assert movimiento.tipo == TipoMovimiento.cashback
    assert notification is not None
    assert notification.mensaje == "Recibiste una recompensa por tu compra."
    assert processed_audit is not None
    assert processed_audit.actor_tipo == "api_key"
    assert processed_audit.actor_api_key_id == api_key.id
    assert {delivery.evento for delivery in deliveries} == {
        "ecommerce.order_paid",
        "ecommerce.order_processed",
        "recompensa.aplicada",
    }


def test_order_paid_deduplica_por_organizacion_proveedor_external_order_id(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _store_rule(db_session, org)
    raw_key = _create_api_key(client, owner, ["ecommerce:write"])
    payload = _order_payload(external_order_id="order-duplicada")

    first = client.post("/api/v1/ext/ecommerce/order-paid", headers={"X-API-Key": raw_key}, json=payload)
    second = client.post("/api/v1/ext/ecommerce/order-paid", headers={"X-API-Key": raw_key}, json=payload)

    assert first.status_code == 201, first.text
    assert second.status_code == 409
    assert second.json()["detail"] == "La orden ya fue procesada."


def test_order_paid_sin_regla_guarda_evento_con_error_claro(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    raw_key = _create_api_key(client, owner, ["ecommerce:write"])

    response = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(external_order_id="order-sin-regla"),
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["recompensa_aplicada"] is None
    assert data["movimiento"] is None
    assert data["event"]["procesado"] is True
    assert data["event"]["error_procesamiento"] == "No hay regla de recompensa aplicable"


def test_order_paid_no_cruza_email_de_otra_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner_a = create_user(db_session, org_a, RolUsuario.owner)
    cliente_b = create_user(db_session, org_b, RolUsuario.cliente)
    _store_rule(db_session, org_a)
    raw_key = _create_api_key(client, owner_a, ["ecommerce:write"])

    response = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(external_order_id="order-cross-email", customer_email=cliente_b.email),
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["event"]["error_procesamiento"] == "El email pertenece a otra organizacion."
    db_session.expire_all()
    assert db_session.scalar(select(Usuario).where(Usuario.email == cliente_b.email, Usuario.organizacion_id == org_a.id)) is None


def test_order_paid_valida_amount_y_currency(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    raw_key = _create_api_key(client, owner, ["ecommerce:write"])

    bad_amount = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(external_order_id="bad-amount", amount="0.00"),
    )
    bad_currency = client.post(
        "/api/v1/ext/ecommerce/order-paid",
        headers={"X-API-Key": raw_key},
        json=_order_payload(external_order_id="bad-currency", currency="EUR"),
    )

    assert bad_amount.status_code == 422
    assert bad_currency.status_code == 400
    assert bad_currency.json()["detail"] == "Moneda no soportada para ecommerce: EUR."


def test_endpoints_internos_listan_por_permisos_y_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner_a = create_user(db_session, org_a, RolUsuario.owner)
    soporte_a = create_user(db_session, org_a, RolUsuario.soporte)
    cliente_a = create_user(db_session, org_a, RolUsuario.cliente)
    event_a = EcommerceOrderEvent(
        organizacion_id=org_a.id,
        proveedor="generic",
        external_order_id="order-a",
        customer_email="a@example.com",
        amount=Decimal("1000.00"),
        currency="ARS",
        status="paid",
        procesado=True,
    )
    event_b = EcommerceOrderEvent(
        organizacion_id=org_b.id,
        proveedor="generic",
        external_order_id="order-b",
        customer_email="b@example.com",
        amount=Decimal("1000.00"),
        currency="ARS",
        status="paid",
        procesado=True,
    )
    db_session.add_all([event_a, event_b])
    db_session.commit()
    db_session.refresh(event_a)
    db_session.refresh(event_b)

    owner_list = client.get("/api/v1/ecommerce/orders", headers=auth_headers(owner_a))
    soporte_list = client.get("/api/v1/ecommerce/orders", headers=auth_headers(soporte_a))
    cliente_list = client.get("/api/v1/ecommerce/orders", headers=auth_headers(cliente_a))
    cross_get = client.get(f"/api/v1/ecommerce/orders/{event_b.id}", headers=auth_headers(owner_a))

    assert owner_list.status_code == 200, owner_list.text
    assert soporte_list.status_code == 200, soporte_list.text
    assert [item["id"] for item in api_data(owner_list)] == [str(event_a.id)]
    assert [item["id"] for item in api_data(soporte_list)] == [str(event_a.id)]
    assert cliente_list.status_code == 403
    assert cross_get.status_code == 404
