from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.auditoria.schemas import AuditActorTipo, AuditLogCreate, AuditLogResponse
from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import is_super_admin


def _normalizar_actor(
    actor_tipo: AuditActorTipo | None,
    actor_usuario_id: UUID | None,
    actor_api_key_id: UUID | None,
) -> tuple[str, UUID | None, UUID | None]:
    tipo = actor_tipo
    if tipo is None:
        if actor_api_key_id is not None:
            tipo = "api_key"
        elif actor_usuario_id is not None:
            tipo = "usuario"
        else:
            tipo = "sistema"
    if tipo == "usuario":
        return tipo, actor_usuario_id, None
    if tipo == "api_key":
        return tipo, None, actor_api_key_id
    return "sistema", None, None


def registrar_evento(
    db: Session,
    *,
    organizacion_id: UUID | None,
    evento: str,
    mensaje: str,
    nivel: str = "INFO",
    actor_tipo: AuditActorTipo | None = None,
    actor_usuario_id: UUID | None = None,
    actor_api_key_id: UUID | None = None,
    endpoint: str | None = None,
    ip: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogResponse:
    tipo, usuario_id, api_key_id = _normalizar_actor(actor_tipo, actor_usuario_id, actor_api_key_id)
    log = AuditLog(
        evento=evento,
        mensaje=mensaje,
        nivel=nivel,
        actor_tipo=tipo,
        actor_usuario_id=usuario_id,
        actor_api_key_id=api_key_id,
        organizacion_id=organizacion_id,
        endpoint=endpoint,
        ip=ip,
        metadata_log=metadata,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return AuditLogResponse.model_validate(log)


def registrar_evento_usuario(
    db: Session,
    *,
    organizacion_id: UUID | None,
    actor_usuario_id: UUID,
    evento: str,
    mensaje: str,
    nivel: str = "INFO",
    endpoint: str | None = None,
    ip: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogResponse:
    return registrar_evento(
        db,
        organizacion_id=organizacion_id,
        evento=evento,
        mensaje=mensaje,
        nivel=nivel,
        actor_tipo="usuario",
        actor_usuario_id=actor_usuario_id,
        endpoint=endpoint,
        ip=ip,
        metadata=metadata,
    )


def registrar_evento_api_key(
    db: Session,
    *,
    organizacion_id: UUID | None,
    actor_api_key_id: UUID,
    evento: str,
    mensaje: str,
    nivel: str = "INFO",
    endpoint: str | None = None,
    ip: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogResponse:
    return registrar_evento(
        db,
        organizacion_id=organizacion_id,
        evento=evento,
        mensaje=mensaje,
        nivel=nivel,
        actor_tipo="api_key",
        actor_api_key_id=actor_api_key_id,
        endpoint=endpoint,
        ip=ip,
        metadata=metadata,
    )


def registrar_evento_sistema(
    db: Session,
    *,
    organizacion_id: UUID | None,
    evento: str,
    mensaje: str,
    nivel: str = "INFO",
    endpoint: str | None = None,
    ip: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogResponse:
    return registrar_evento(
        db,
        organizacion_id=organizacion_id,
        evento=evento,
        mensaje=mensaje,
        nivel=nivel,
        actor_tipo="sistema",
        endpoint=endpoint,
        ip=ip,
        metadata=metadata,
    )


def registrar_audit_log(datos: AuditLogCreate, db: Session) -> AuditLogResponse:
    return registrar_evento(
        db,
        organizacion_id=datos.organizacion_id,
        evento=datos.evento,
        mensaje=datos.mensaje,
        nivel=datos.nivel,
        actor_tipo=datos.actor_tipo,
        actor_usuario_id=datos.actor_usuario_id,
        actor_api_key_id=datos.actor_api_key_id,
        endpoint=datos.endpoint,
        ip=datos.ip,
        metadata=datos.metadata,
    )


def listar_audit_logs(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AuditLogResponse]:
    query = select(AuditLog)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(AuditLog.organizacion_id == organizacion_id)
    else:
        query = query.where(AuditLog.organizacion_id == current_user.organizacion_id)
    logs = db.scalars(query.order_by(AuditLog.fecha.desc()).offset(skip).limit(limit)).all()
    return [AuditLogResponse.model_validate(log) for log in logs]
