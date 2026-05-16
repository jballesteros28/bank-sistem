from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import httpx
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.schemas import AuditLogCreate
from app.apps.auditoria.services import registrar_audit_log
from app.apps.integraciones.models import WebhookDelivery, WebhookEndpoint
from app.apps.integraciones.schemas import ALLOWED_WEBHOOK_EVENTS
from app.apps.integraciones.services import decrypt_secret
from app.core.database import SessionLocal


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def construir_payload_evento(evento: str, organizacion_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "evento": evento,
        "organizacion_id": str(organizacion_id),
        "fecha": _now().isoformat(),
        "data": _jsonable(data),
    }


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def firmar_payload(payload: dict[str, Any], secret: str) -> str:
    import hashlib
    import hmac

    signature = hmac.new(secret.encode("utf-8"), _canonical_payload(payload), hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def encolar_webhook_evento(
    *,
    evento: str,
    organizacion_id: UUID,
    data: dict[str, Any],
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> list[WebhookDelivery]:
    if evento not in ALLOWED_WEBHOOK_EVENTS:
        return []
    endpoints = db.scalars(
        select(WebhookEndpoint).where(
            WebhookEndpoint.organizacion_id == organizacion_id,
            WebhookEndpoint.activo.is_(True),
        )
    ).all()
    payload = construir_payload_evento(evento, organizacion_id, data)
    deliveries: list[WebhookDelivery] = []
    for endpoint in endpoints:
        if evento not in (endpoint.eventos or []):
            continue
        delivery = WebhookDelivery(
            organizacion_id=organizacion_id,
            webhook_endpoint_id=endpoint.id,
            evento=evento,
            payload=payload,
            status="pendiente",
            intentos=0,
        )
        db.add(delivery)
        deliveries.append(delivery)
    if not deliveries:
        return []
    db.commit()
    for delivery in deliveries:
        db.refresh(delivery)
        if background_tasks is not None:
            background_tasks.add_task(enviar_webhook_delivery, delivery.id, db)
    return deliveries


def _audit_delivery(db: Session, delivery: WebhookDelivery, *, success: bool) -> None:
    try:
        registrar_audit_log(
            AuditLogCreate(
                evento="webhook_enviado" if success else "webhook_fallido",
                mensaje="Webhook enviado." if success else "Webhook fallido.",
                nivel="INFO" if success else "ERROR",
                organizacion_id=delivery.organizacion_id,
                metadata={
                    "delivery_id": str(delivery.id),
                    "webhook_endpoint_id": str(delivery.webhook_endpoint_id),
                    "evento": delivery.evento,
                    "status": delivery.status,
                    "status_code": delivery.status_code,
                    "intentos": delivery.intentos,
                },
            ),
            db,
        )
    except Exception:
        db.rollback()


def _send_delivery(delivery_id: UUID, db: Session) -> None:
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        return
    endpoint = db.get(WebhookEndpoint, delivery.webhook_endpoint_id)
    if endpoint is None or not endpoint.activo:
        delivery.status = "fallido"
        delivery.error = "Webhook endpoint inactivo."
        delivery.fecha_ultimo_intento = _now()
        db.add(delivery)
        db.commit()
        _audit_delivery(db, delivery, success=False)
        return

    delivery.intentos += 1
    delivery.fecha_ultimo_intento = _now()
    secret = decrypt_secret(endpoint.secret_encrypted)
    headers = {
        "Content-Type": "application/json",
        "X-Wallet-Signature": firmar_payload(delivery.payload, secret),
        "X-Wallet-Event": delivery.evento,
        "X-Wallet-Delivery-Id": str(delivery.id),
    }
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.post(endpoint.url, json=delivery.payload, headers=headers)
        delivery.status_code = response.status_code
        delivery.respuesta_body = response.text[:2000]
        if 200 <= response.status_code < 300:
            delivery.status = "enviado"
            delivery.error = None
        else:
            delivery.status = "fallido"
            delivery.error = f"HTTP {response.status_code}"
    except Exception as exc:
        delivery.status = "fallido"
        delivery.error = str(exc)[:1000]
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    _audit_delivery(db, delivery, success=delivery.status == "enviado")


def enviar_webhook_delivery(delivery_id: UUID, db: Session | None = None) -> None:
    if db is not None:
        _send_delivery(delivery_id, db)
        return
    session = SessionLocal()
    try:
        _send_delivery(delivery_id, session)
    finally:
        session.close()
