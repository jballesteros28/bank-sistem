from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.schemas import AuditActorTipo
from app.apps.auditoria.services import registrar_evento
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.integraciones.models import APIKey, WebhookDelivery, WebhookEndpoint
from app.apps.integraciones.schemas import (
    ALLOWED_API_KEY_SCOPES,
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyRevokeResponse,
    WebhookDeliveryResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
)
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.services import obtener_o_asignar_plan_organizacion
from app.core.config import settings
from app.core.permissions import is_admin, is_super_admin
from app.shared.enums import EstadoOrganizacion


KEY_PREFIX_LENGTH = 20


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_integration_admin(current_user: DatosUsuarioToken, *, write: bool = False) -> None:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")
    if write and current_user.organizacion_id is None and not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")


def _resolve_organization_for_user(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> Organizacion:
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar una organizacion.")
    organizacion = db.get(Organizacion, scope_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return organizacion


def _hash_value(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _legacy_encryption_key() -> bytes:
    return hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def _legacy_encrypt_secret(secret: str) -> str:
    data = secret.encode("utf-8")
    key = _legacy_encryption_key()
    encrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode("ascii")


def _legacy_decrypt_secret(encrypted: str) -> str:
    data = base64.urlsafe_b64decode(encrypted.encode("ascii"))
    key = _legacy_encryption_key()
    decrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    return decrypted.decode("utf-8")


def encrypt_webhook_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt_webhook_secret(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return _legacy_decrypt_secret(encrypted)


encrypt_secret = encrypt_webhook_secret
decrypt_secret = decrypt_webhook_secret


def _audit(
    db: Session,
    *,
    evento: str,
    mensaje: str,
    organizacion_id: UUID | None,
    actor_tipo: AuditActorTipo | None = None,
    actor_usuario_id: UUID | None = None,
    actor_api_key_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    nivel: str = "INFO",
) -> None:
    try:
        registrar_evento(
            db,
            organizacion_id=organizacion_id,
            evento=evento,
            mensaje=mensaje,
            nivel=nivel,
            actor_tipo=actor_tipo,
            actor_usuario_id=actor_usuario_id,
            actor_api_key_id=actor_api_key_id,
            metadata=metadata,
        )
    except Exception:
        db.rollback()


def _generate_api_key() -> str:
    return f"wsk_test_{secrets.token_urlsafe(32)}"


def crear_api_key(datos: APIKeyCreate, current_user: DatosUsuarioToken, db: Session) -> APIKeyCreateResponse:
    _ensure_integration_admin(current_user, write=True)
    organizacion = _resolve_organization_for_user(current_user, db, datos.organizacion_id)
    raw_key = _generate_api_key()
    api_key = APIKey(
        organizacion_id=organizacion.id,
        nombre=datos.nombre,
        key_prefix=raw_key[:KEY_PREFIX_LENGTH],
        key_hash=_hash_value(raw_key),
        scopes=datos.scopes,
        activa=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    _audit(
        db,
        evento="api_key_creada",
        mensaje="API Key creada.",
        actor_usuario_id=current_user.id,
        organizacion_id=organizacion.id,
        metadata={"api_key_id": str(api_key.id), "key_prefix": api_key.key_prefix, "scopes": api_key.scopes},
    )
    return APIKeyCreateResponse(**APIKeyResponse.model_validate(api_key).model_dump(), api_key=raw_key)


def listar_api_keys(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[APIKeyResponse]:
    _ensure_integration_admin(current_user)
    query = select(APIKey).order_by(APIKey.fecha_creacion.desc())
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(APIKey.organizacion_id == organizacion_id)
    else:
        if organizacion_id is not None and organizacion_id != current_user.organizacion_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")
        query = query.where(APIKey.organizacion_id == current_user.organizacion_id)
    return [APIKeyResponse.model_validate(api_key) for api_key in db.scalars(query).all()]


def _get_api_key_scoped(
    api_key_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> APIKey:
    api_key = db.get(APIKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key no encontrada.")
    if not is_super_admin(current_user.rol) and api_key.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key no encontrada.")
    return api_key


def revocar_api_key(
    api_key_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> APIKeyRevokeResponse:
    _ensure_integration_admin(current_user, write=True)
    api_key = _get_api_key_scoped(api_key_id, current_user, db)
    api_key.activa = False
    api_key.fecha_revocacion = _now()
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    _audit(
        db,
        evento="api_key_revocada",
        mensaje="API Key revocada.",
        actor_usuario_id=current_user.id,
        organizacion_id=api_key.organizacion_id,
        metadata={"api_key_id": str(api_key.id), "key_prefix": api_key.key_prefix},
    )
    return APIKeyRevokeResponse(
        id=api_key.id,
        activa=api_key.activa,
        fecha_revocacion=api_key.fecha_revocacion or _now(),
        mensaje="API Key revocada.",
    )


def validar_api_key(raw_key: str, db: Session) -> APIKey:
    if not raw_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key requerida.")
    key_prefix = raw_key[:KEY_PREFIX_LENGTH]
    api_key = db.scalar(select(APIKey).where(APIKey.key_prefix == key_prefix))
    if api_key is None or not hmac.compare_digest(api_key.key_hash, _hash_value(raw_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key invalida.")
    if not api_key.activa:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key revocada.")
    organizacion = db.get(Organizacion, api_key.organizacion_id)
    if organizacion is None or organizacion.estado != EstadoOrganizacion.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizacion inactiva.")
    api_key.ultimo_uso_en = _now()
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def verificar_scope(api_key: APIKey, scope: str) -> None:
    if scope not in ALLOWED_API_KEY_SCOPES:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Scope interno invalido.")
    if scope not in (api_key.scopes or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Scope requerido: {scope}.")


def registrar_uso_api_key(
    api_key: APIKey,
    db: Session,
    *,
    endpoint: str,
    scope: str,
) -> None:
    _audit(
        db,
        evento="api_key_usada",
        mensaje="API Key usada en endpoint externo.",
        organizacion_id=api_key.organizacion_id,
        actor_tipo="api_key",
        actor_api_key_id=api_key.id,
        metadata={
            "api_key_id": str(api_key.id),
            "key_prefix": api_key.key_prefix,
            "endpoint": endpoint,
            "scope": scope,
        },
    )


def _ensure_webhooks_allowed(db: Session, organizacion: Organizacion) -> None:
    plan = obtener_o_asignar_plan_organizacion(db, organizacion)
    if not plan.permite_webhooks:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El plan {plan.codigo} no permite webhooks.",
        )


def crear_webhook_endpoint(
    datos: WebhookEndpointCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WebhookEndpointResponse:
    _ensure_integration_admin(current_user, write=True)
    organizacion = _resolve_organization_for_user(current_user, db, datos.organizacion_id)
    _ensure_webhooks_allowed(db, organizacion)
    webhook = WebhookEndpoint(
        organizacion_id=organizacion.id,
        nombre=datos.nombre,
        url=str(datos.url),
        eventos=datos.eventos,
        secret_encrypted=encrypt_webhook_secret(datos.secret),
        activo=True,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    _audit(
        db,
        evento="webhook_creado",
        mensaje="Webhook creado.",
        actor_usuario_id=current_user.id,
        organizacion_id=organizacion.id,
        metadata={"webhook_id": str(webhook.id), "eventos": webhook.eventos, "url": webhook.url},
    )
    return WebhookEndpointResponse.model_validate(webhook)


def listar_webhook_endpoints(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[WebhookEndpointResponse]:
    _ensure_integration_admin(current_user)
    query = select(WebhookEndpoint).order_by(WebhookEndpoint.fecha_creacion.desc())
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(WebhookEndpoint.organizacion_id == organizacion_id)
    else:
        if organizacion_id is not None and organizacion_id != current_user.organizacion_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")
        query = query.where(WebhookEndpoint.organizacion_id == current_user.organizacion_id)
    return [WebhookEndpointResponse.model_validate(webhook) for webhook in db.scalars(query).all()]


def _get_webhook_scoped(
    webhook_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WebhookEndpoint:
    webhook = db.get(WebhookEndpoint, webhook_id)
    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook no encontrado.")
    if not is_super_admin(current_user.rol) and webhook.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook no encontrado.")
    return webhook


def actualizar_webhook_endpoint(
    webhook_id: UUID,
    datos: WebhookEndpointUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WebhookEndpointResponse:
    _ensure_integration_admin(current_user, write=True)
    webhook = _get_webhook_scoped(webhook_id, current_user, db)
    cambios = datos.model_dump(exclude_unset=True)
    if "url" in cambios and cambios["url"] is not None:
        webhook.url = str(cambios["url"])
    if "secret" in cambios and cambios["secret"] is not None:
        webhook.secret_encrypted = encrypt_webhook_secret(cambios["secret"])
    for field in ("nombre", "eventos", "activo"):
        if field in cambios:
            setattr(webhook, field, cambios[field])
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    _audit(
        db,
        evento="webhook_actualizado",
        mensaje="Webhook actualizado.",
        actor_usuario_id=current_user.id,
        organizacion_id=webhook.organizacion_id,
        metadata={"webhook_id": str(webhook.id), "eventos": webhook.eventos, "activo": webhook.activo},
    )
    return WebhookEndpointResponse.model_validate(webhook)


def desactivar_webhook_endpoint(
    webhook_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WebhookEndpointResponse:
    _ensure_integration_admin(current_user, write=True)
    webhook = _get_webhook_scoped(webhook_id, current_user, db)
    webhook.activo = False
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    _audit(
        db,
        evento="webhook_desactivado",
        mensaje="Webhook desactivado.",
        actor_usuario_id=current_user.id,
        organizacion_id=webhook.organizacion_id,
        metadata={"webhook_id": str(webhook.id)},
    )
    return WebhookEndpointResponse.model_validate(webhook)


def listar_webhook_deliveries(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    webhook_endpoint_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[WebhookDeliveryResponse]:
    _ensure_integration_admin(current_user)
    query = select(WebhookDelivery).order_by(WebhookDelivery.fecha_creacion.desc())
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(WebhookDelivery.organizacion_id == organizacion_id)
    else:
        if organizacion_id is not None and organizacion_id != current_user.organizacion_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")
        query = query.where(WebhookDelivery.organizacion_id == current_user.organizacion_id)
    if webhook_endpoint_id is not None:
        query = query.where(WebhookDelivery.webhook_endpoint_id == webhook_endpoint_id)
    deliveries = db.scalars(query.offset(skip).limit(limit)).all()
    return [WebhookDeliveryResponse.model_validate(delivery) for delivery in deliveries]


def _get_delivery_scoped(
    delivery_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WebhookDelivery:
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery no encontrado.")
    if not is_super_admin(current_user.rol) and delivery.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery no encontrado.")
    return delivery


def reenviar_webhook_delivery(
    delivery_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
    background_tasks: BackgroundTasks,
) -> WebhookDeliveryResponse:
    _ensure_integration_admin(current_user, write=True)
    delivery = _get_delivery_scoped(delivery_id, current_user, db)
    if delivery.status not in {"fallido", "pendiente"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden reenviar deliveries fallidos o pendientes.",
        )
    delivery.status = "pendiente"
    delivery.error = None
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    _audit(
        db,
        evento="webhook_reenvio_agendado",
        mensaje="Reenvio manual de webhook agendado.",
        actor_usuario_id=current_user.id,
        organizacion_id=delivery.organizacion_id,
        metadata={
            "delivery_id": str(delivery.id),
            "webhook_endpoint_id": str(delivery.webhook_endpoint_id),
            "evento": delivery.evento,
            "intentos": delivery.intentos,
        },
    )

    from app.apps.integraciones.webhook_dispatcher import enviar_webhook_delivery

    background_tasks.add_task(enviar_webhook_delivery, delivery.id)
    return WebhookDeliveryResponse.model_validate(delivery)
