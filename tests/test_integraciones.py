from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.integraciones.models import APIKey, WebhookDelivery
from app.apps.integraciones.webhook_dispatcher import firmar_payload
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.planes.services import asegurar_planes_base, obtener_plan_por_codigo
from app.apps.wallets.models import Wallet
from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet


def _assign_plan(db: Session, org: Organizacion, code: str) -> Plan:
    asegurar_planes_base(db)
    plan = obtener_plan_por_codigo(code, db)
    assert plan is not None
    org.plan_id = plan.id
    db.add(org)
    db.commit()
    db.refresh(org)
    return plan


def _create_api_key(
    client: TestClient,
    user,
    scopes: list[str],
) -> tuple[str, dict[str, object]]:
    response = client.post(
        "/api/v1/integraciones/api-keys",
        headers=auth_headers(user),
        json={"nombre": "ERP", "scopes": scopes},
    )
    assert response.status_code == 201, response.text
    data = api_data(response)
    return str(data["api_key"]), data


def test_owner_crea_api_key_y_listado_no_expone_secretos(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    raw_key, created = _create_api_key(client, owner, ["wallets:read", "movimientos:write"])
    listed = client.get("/api/v1/integraciones/api-keys", headers=auth_headers(owner))

    assert raw_key.startswith("wsk_test_")
    assert created["key_prefix"] == raw_key[:20]
    assert "key_hash" not in created
    assert listed.status_code == 200, listed.text
    listed_data = api_data(listed)
    assert listed_data[0]["key_prefix"] == raw_key[:20]
    assert "api_key" not in listed_data[0]
    assert "key_hash" not in listed_data[0]
    stored = db_session.scalar(select(APIKey).where(APIKey.id == UUID(str(created["id"]))))
    assert stored is not None
    assert stored.key_hash != raw_key


def test_soporte_y_cliente_no_pueden_crear_api_key(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org, RolUsuario.cliente)
    payload = {"nombre": "ERP", "scopes": ["wallets:read"]}

    soporte_response = client.post("/api/v1/integraciones/api-keys", headers=auth_headers(soporte), json=payload)
    cliente_response = client.post("/api/v1/integraciones/api-keys", headers=auth_headers(cliente), json=payload)

    assert soporte_response.status_code == 403
    assert cliente_response.status_code == 403


def test_key_revocada_no_autentica(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_wallet(db_session, owner)
    raw_key, created = _create_api_key(client, owner, ["wallets:read"])

    ok_response = client.get(f"/api/v1/ext/wallets/{wallet.id}", headers={"X-API-Key": raw_key})
    revoked = client.delete(f"/api/v1/integraciones/api-keys/{created['id']}", headers=auth_headers(owner))
    blocked = client.get(f"/api/v1/ext/wallets/{wallet.id}", headers={"X-API-Key": raw_key})

    assert ok_response.status_code == 200, ok_response.text
    assert revoked.status_code == 200, revoked.text
    assert api_data(revoked)["activa"] is False
    assert blocked.status_code == 401


def test_scope_faltante_bloquea_endpoint_externo(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_wallet(db_session, owner)
    raw_key, _ = _create_api_key(client, owner, ["wallets:read"])

    response = client.post(
        "/api/v1/ext/movimientos/deposito",
        headers={"X-API-Key": raw_key},
        json={"wallet_destino_id": str(wallet.id), "monto": "10.00"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Scope requerido: movimientos:write."


def test_scope_correcto_permite_endpoint_externo_y_audita_uso(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_wallet(db_session, owner)
    raw_key, _ = _create_api_key(client, owner, ["movimientos:write", "movimientos:read"])

    response = client.post(
        "/api/v1/ext/movimientos/deposito",
        headers={"X-API-Key": raw_key},
        json={"wallet_destino_id": str(wallet.id), "monto": "12.00"},
    )
    listed = client.get("/api/v1/ext/movimientos", headers={"X-API-Key": raw_key})

    assert response.status_code == 201, response.text
    assert api_data(response)["wallet_origen_id"] is None
    db_session.expire_all()
    assert db_session.get(Wallet, wallet.id).saldo == Decimal("12.00")
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in api_data(listed)] == [api_data(response)["id"]]
    audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "api_key_usada"))
    assert audit is not None


def test_api_key_no_opera_wallets_de_otra_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner = create_user(db_session, org_a, RolUsuario.owner)
    user_b = create_user(db_session, org_b)
    wallet_b = create_wallet(db_session, user_b)
    raw_key, _ = _create_api_key(client, owner, ["wallets:read"])

    response = client.get(f"/api/v1/ext/wallets/{wallet_b.id}", headers={"X-API-Key": raw_key})

    assert response.status_code == 404


def test_owner_crea_webhook_si_plan_permite_y_no_expone_secret(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _assign_plan(db_session, org, "pro")

    response = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={
            "nombre": "ERP",
            "url": "https://example.com/hook",
            "eventos": ["wallet.creada", "movimiento.creado"],
            "secret": "secret-webhook-123",
        },
    )

    assert response.status_code == 201, response.text
    data = api_data(response)
    assert data["eventos"] == ["movimiento.creado", "wallet.creada"]
    assert "secret" not in data
    assert "secret_encrypted" not in data


def test_free_no_puede_crear_webhook(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={
            "nombre": "ERP",
            "url": "https://example.com/hook",
            "eventos": ["wallet.creada"],
            "secret": "secret-webhook-123",
        },
    )

    assert response.status_code == 403
    assert "no permite webhooks" in response.json()["detail"]


def test_webhook_endpoint_invalido_y_evento_invalido_fallan(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _assign_plan(db_session, org, "pro")

    bad_url = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={"nombre": "ERP", "url": "not-a-url", "eventos": ["wallet.creada"], "secret": "secret-webhook-123"},
    )
    bad_event = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={
            "nombre": "ERP",
            "url": "https://example.com/hook",
            "eventos": ["wallet.borrada"],
            "secret": "secret-webhook-123",
        },
    )

    assert bad_url.status_code == 422
    assert bad_event.status_code == 422


def test_delivery_se_crea_y_firma_al_disparar_evento_wallet(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _assign_plan(db_session, org, "pro")
    secret = "secret-webhook-123"
    calls: list[dict[str, object]] = []

    class DummyResponse:
        status_code = 204
        text = ""

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url, json, headers):
            calls.append({"url": url, "json": json, "headers": headers})
            return DummyResponse()

    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.httpx.Client", FakeClient)
    webhook = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={"nombre": "ERP", "url": "https://example.com/hook", "eventos": ["wallet.creada"], "secret": secret},
    )
    assert webhook.status_code == 201, webhook.text

    created = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Integrada", "tipo": "principal", "moneda": "ARS"},
    )

    assert created.status_code == 201, created.text
    delivery = db_session.scalar(select(WebhookDelivery).where(WebhookDelivery.evento == "wallet.creada"))
    assert delivery is not None
    assert delivery.status == "enviado"
    assert calls
    headers = calls[0]["headers"]
    assert headers["X-Wallet-Event"] == "wallet.creada"
    assert headers["X-Wallet-Delivery-Id"] == str(delivery.id)
    assert headers["X-Wallet-Signature"] == firmar_payload(delivery.payload, secret)


def test_fallo_de_webhook_no_rompe_movimiento(client: TestClient, db_session: Session, monkeypatch) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_wallet(db_session, owner)
    _assign_plan(db_session, org, "pro")

    class FailingClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url, json, headers):
            raise RuntimeError("endpoint down")

    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.httpx.Client", FailingClient)
    webhook = client.post(
        "/api/v1/integraciones/webhooks",
        headers=auth_headers(owner),
        json={
            "nombre": "ERP",
            "url": "https://example.com/hook",
            "eventos": ["movimiento.creado"],
            "secret": "secret-webhook-123",
        },
    )
    assert webhook.status_code == 201, webhook.text

    movement = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(owner),
        json={"wallet_destino_id": str(wallet.id), "monto": "9.00"},
    )

    assert movement.status_code == 201, movement.text
    db_session.expire_all()
    assert db_session.get(Wallet, wallet.id).saldo == Decimal("9.00")
    delivery = db_session.scalar(select(WebhookDelivery).where(WebhookDelivery.evento == "movimiento.creado"))
    assert delivery is not None
    assert delivery.status == "fallido"
    assert "endpoint down" in str(delivery.error)
