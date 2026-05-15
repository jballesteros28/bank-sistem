from __future__ import annotations

import inspect
from pathlib import Path

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.movimientos.routes import post_deposito
from app.apps.notificaciones.models import Notificacion
from app.apps.notificaciones.services import crear_notificacion_interna
from app.apps.onboarding.routes import post_registro_organizacion
from app.apps.wallets.routes import post_wallet
from app.core.config import settings
from app.shared.enums import CanalNotificacion, RolUsuario, TipoNotificacion
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet, onboarding_payload


def _notificaciones(db: Session) -> list[Notificacion]:
    return db.scalars(select(Notificacion).order_by(Notificacion.fecha_creacion.asc())).all()


def test_onboarding_crea_notificacion_interna_y_no_envia_email_real(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_send(*args, **kwargs) -> None:
        calls.append("send")

    monkeypatch.setattr("app.apps.notificaciones.email_service.enviar_email", fake_send)

    response = client.post("/api/v1/onboarding/registro-organizacion", json=onboarding_payload())

    assert response.status_code == 201, response.text
    internas = [
        item
        for item in _notificaciones(db_session)
        if item.tipo == TipoNotificacion.onboarding_exitoso and item.canal == CanalNotificacion.interna
    ]
    assert len(internas) == 1
    assert calls == []


def test_crear_wallet_genera_notificacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Nueva", "tipo": "ahorro", "moneda": "ARS"},
    )

    assert response.status_code == 201, response.text
    notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.tipo == TipoNotificacion.wallet_creada,
            Notificacion.canal == CanalNotificacion.interna,
            Notificacion.usuario_id == owner.id,
        )
    )
    assert notification is not None


def test_movimiento_genera_notificacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    cliente = create_user(db_session, org)
    wallet = create_wallet(db_session, cliente)

    response = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "20.00"},
    )

    assert response.status_code == 201, response.text
    notification = db_session.scalar(
        select(Notificacion).where(
            Notificacion.tipo == TipoNotificacion.movimiento_deposito,
            Notificacion.canal == CanalNotificacion.interna,
            Notificacion.usuario_id == cliente.id,
        )
    )
    assert notification is not None


def test_listar_notificaciones_respeta_usuario_y_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    user_a = create_user(db_session, org)
    user_b = create_user(db_session, org)
    crear_notificacion_interna(
        organizacion_id=org.id,
        usuario_id=user_a.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Aviso A",
        mensaje="Mensaje A",
        db=db_session,
    )
    crear_notificacion_interna(
        organizacion_id=org.id,
        usuario_id=user_b.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Aviso B",
        mensaje="Mensaje B",
        db=db_session,
    )

    user_response = client.get("/api/v1/notificaciones", headers=auth_headers(user_a))
    admin_response = client.get("/api/v1/notificaciones", headers=auth_headers(admin))

    assert user_response.status_code == 200, user_response.text
    assert [item["titulo"] for item in api_data(user_response)["items"]] == ["Aviso A"]
    assert admin_response.status_code == 200, admin_response.text
    assert {item["titulo"] for item in api_data(admin_response)["items"]} == {"Aviso A", "Aviso B"}


def test_usuario_no_ve_notificaciones_de_otra_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    user_a = create_user(db_session, org_a)
    user_b = create_user(db_session, org_b)
    crear_notificacion_interna(
        organizacion_id=org_b.id,
        usuario_id=user_b.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Privada",
        mensaje="Otra organizacion",
        db=db_session,
    )

    response = client.get("/api/v1/notificaciones", headers=auth_headers(user_a))

    assert response.status_code == 200, response.text
    assert api_data(response)["items"] == []


def test_marcar_notificacion_como_leida(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    user = create_user(db_session, org)
    notification = crear_notificacion_interna(
        organizacion_id=org.id,
        usuario_id=user.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Seguridad",
        mensaje="Acceso nuevo",
        db=db_session,
    )

    response = client.patch(f"/api/v1/notificaciones/{notification.id}/leida", headers=auth_headers(user))

    assert response.status_code == 200, response.text
    assert api_data(response)["leida"] is True
    db_session.expire_all()
    assert db_session.get(Notificacion, notification.id).leida is True
    audit_log = db_session.scalar(select(AuditLog).where(AuditLog.actor_usuario_id == user.id))
    assert audit_log is not None
    assert audit_log.actor_usuario_id == user.id


def test_contar_no_leidas(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    user = create_user(db_session, org)
    leida = crear_notificacion_interna(
        organizacion_id=org.id,
        usuario_id=user.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Leida",
        mensaje="Uno",
        db=db_session,
    )
    crear_notificacion_interna(
        organizacion_id=org.id,
        usuario_id=user.id,
        tipo=TipoNotificacion.seguridad,
        titulo="Pendiente",
        mensaje="Dos",
        db=db_session,
    )
    client.patch(f"/api/v1/notificaciones/{leida.id}/leida", headers=auth_headers(user))

    response = client.get("/api/v1/notificaciones/no-leidas/count", headers=auth_headers(user))

    assert response.status_code == 200, response.text
    assert api_data(response) == 1


def test_error_de_email_no_rompe_operacion_principal(client: TestClient, db_session: Session, monkeypatch) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    monkeypatch.setattr(settings, "EMAILS_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "MAIL_FROM", "wallet@example.com")
    monkeypatch.setattr(settings, "MAIL_SERVER", "smtp.example.com")

    def fail_send(*args, **kwargs) -> None:
        raise RuntimeError("smtp down")

    monkeypatch.setattr("app.apps.notificaciones.email_service.enviar_email", fail_send)

    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Email falla", "tipo": "ahorro", "moneda": "ARS"},
    )

    assert response.status_code == 201, response.text


def test_background_tasks_en_endpoints_relevantes() -> None:
    for endpoint in (post_registro_organizacion, post_wallet, post_deposito):
        parameter = inspect.signature(endpoint).parameters["background_tasks"]
        assert parameter.annotation is BackgroundTasks


def test_templates_html_existen() -> None:
    template_dir = Path("app/apps/notificaciones/templates")
    expected = {
        "base.html",
        "onboarding_exitoso.html",
        "wallet_creada.html",
        "movimiento.html",
        "wallet_congelada.html",
        "organizacion_suspendida.html",
    }

    assert expected <= {item.name for item in template_dir.iterdir()}
