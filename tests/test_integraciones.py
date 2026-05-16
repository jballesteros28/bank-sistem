from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.integraciones.models import APIKey, WebhookDelivery, WebhookEndpoint
from app.apps.integraciones.services import decrypt_webhook_secret, encrypt_webhook_secret
from app.apps.integraciones.webhook_dispatcher import encolar_webhook_evento, enviar_webhook_delivery, firmar_payload
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


def _store_webhook_endpoint(
    db: Session,
    org: Organizacion,
    *,
    eventos: list[str],
    secret: str = "secret-webhook-123",
    activo: bool = True,
) -> WebhookEndpoint:
    endpoint = WebhookEndpoint(
        organizacion_id=org.id,
        nombre="ERP",
        url="https://example.com/hook",
        eventos=eventos,
        secret_encrypted=encrypt_webhook_secret(secret),
        activo=activo,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def _store_webhook_delivery(
    db: Session,
    org: Organizacion,
    endpoint: WebhookEndpoint,
    *,
    status: str = "fallido",
    intentos: int = 1,
) -> WebhookDelivery:
    delivery = WebhookDelivery(
        organizacion_id=org.id,
        webhook_endpoint_id=endpoint.id,
        evento="wallet.creada",
        payload={"evento": "wallet.creada", "data": {"id": "w1"}},
        status=status,
        intentos=intentos,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


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
    api_key = db_session.scalar(select(APIKey).where(APIKey.key_prefix == raw_key[:20]))
    assert api_key is not None
    audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "api_key_usada"))
    assert audit is not None
    assert audit.actor_tipo == "api_key"
    assert audit.actor_api_key_id == api_key.id
    assert audit.actor_usuario_id is None
    movement_audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "movimiento_registrado"))
    assert movement_audit is not None
    assert movement_audit.actor_tipo == "api_key"
    assert movement_audit.actor_api_key_id == api_key.id
    assert movement_audit.actor_usuario_id is None
    assert db_session.scalar(select(AuditLog).where(AuditLog.actor_usuario_id == api_key.id)) is None


def test_endpoint_externo_cashback_registra_auditoria_con_api_key(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_wallet(db_session, owner)
    raw_key, _ = _create_api_key(client, owner, ["movimientos:write"])

    response = client.post(
        "/api/v1/ext/movimientos/cashback",
        headers={"X-API-Key": raw_key},
        json={"wallet_destino_id": str(wallet.id), "monto": "5.00"},
    )

    assert response.status_code == 201, response.text
    api_key = db_session.scalar(select(APIKey).where(APIKey.key_prefix == raw_key[:20]))
    assert api_key is not None
    movement_audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "movimiento_registrado"))
    assert movement_audit is not None
    assert movement_audit.actor_tipo == "api_key"
    assert movement_audit.actor_api_key_id == api_key.id
    assert movement_audit.actor_usuario_id is None


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
    stored = db_session.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id == UUID(str(data["id"]))))
    assert stored is not None
    assert stored.secret_encrypted != "secret-webhook-123"
    assert decrypt_webhook_secret(stored.secret_encrypted) == "secret-webhook-123"


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
    audit = db_session.scalar(select(AuditLog).where(AuditLog.evento == "webhook_enviado"))
    assert audit is not None
    assert audit.actor_tipo == "sistema"
    assert audit.actor_usuario_id is None
    assert audit.actor_api_key_id is None


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


def test_webhook_background_task_se_agenda_sin_sesion_db(db_session: Session) -> None:
    org = create_org(db_session)
    _store_webhook_endpoint(db_session, org, eventos=["wallet.creada"])
    background_tasks = BackgroundTasks()

    deliveries = encolar_webhook_evento(
        evento="wallet.creada",
        organizacion_id=org.id,
        data={"wallet_id": "w1"},
        db=db_session,
        background_tasks=background_tasks,
    )

    assert len(deliveries) == 1
    assert len(background_tasks.tasks) == 1
    task = background_tasks.tasks[0]
    assert task.func is enviar_webhook_delivery
    assert task.args == (deliveries[0].id,)


def test_webhook_delivery_se_envia_usando_sesion_nueva(db_session: Session, monkeypatch) -> None:
    org = create_org(db_session)
    endpoint = _store_webhook_endpoint(db_session, org, eventos=["wallet.creada"])
    delivery = _store_webhook_delivery(db_session, org, endpoint, status="pendiente", intentos=0)

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
            return DummyResponse()

    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.httpx.Client", FakeClient)

    enviar_webhook_delivery(delivery.id)

    db_session.expire_all()
    stored = db_session.get(WebhookDelivery, delivery.id)
    assert stored is not None
    assert stored.status == "enviado"
    assert stored.intentos == 1


def test_delivery_fallido_puede_reenviarse(client: TestClient, db_session: Session, monkeypatch) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    endpoint = _store_webhook_endpoint(db_session, org, eventos=["wallet.creada"])
    delivery = _store_webhook_delivery(db_session, org, endpoint, status="fallido", intentos=1)

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
            return DummyResponse()

    monkeypatch.setattr("app.apps.integraciones.webhook_dispatcher.httpx.Client", FakeClient)

    response = client.post(
        f"/api/v1/integraciones/webhooks/deliveries/{delivery.id}/reenviar",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    stored = db_session.get(WebhookDelivery, delivery.id)
    assert stored is not None
    assert stored.status == "enviado"
    assert stored.intentos == 2


def test_delivery_enviado_no_se_reenvia(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    endpoint = _store_webhook_endpoint(db_session, org, eventos=["wallet.creada"])
    delivery = _store_webhook_delivery(db_session, org, endpoint, status="enviado", intentos=1)

    response = client.post(
        f"/api/v1/integraciones/webhooks/deliveries/{delivery.id}/reenviar",
        headers=auth_headers(owner),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se pueden reenviar deliveries fallidos o pendientes."


def test_soporte_no_puede_reenviar_delivery(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    endpoint = _store_webhook_endpoint(db_session, org, eventos=["wallet.creada"])
    delivery = _store_webhook_delivery(db_session, org, endpoint)

    response = client.post(
        f"/api/v1/integraciones/webhooks/deliveries/{delivery.id}/reenviar",
        headers=auth_headers(soporte),
    )

    assert response.status_code == 403


def test_owner_no_puede_reenviar_delivery_de_otra_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner = create_user(db_session, org_a, RolUsuario.owner)
    endpoint_b = _store_webhook_endpoint(db_session, org_b, eventos=["wallet.creada"])
    delivery_b = _store_webhook_delivery(db_session, org_b, endpoint_b)

    response = client.post(
        f"/api/v1/integraciones/webhooks/deliveries/{delivery_b.id}/reenviar",
        headers=auth_headers(owner),
    )

    assert response.status_code == 404
