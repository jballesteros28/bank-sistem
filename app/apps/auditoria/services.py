from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog
from app.apps.auditoria.schemas import AuditLogCreate, AuditLogResponse
from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import is_super_admin


def registrar_audit_log(datos: AuditLogCreate, db: Session) -> AuditLogResponse:
    log = AuditLog(
        evento=datos.evento,
        mensaje=datos.mensaje,
        nivel=datos.nivel,
        actor_usuario_id=datos.actor_usuario_id,
        organizacion_id=datos.organizacion_id,
        endpoint=datos.endpoint,
        ip=datos.ip,
        metadata_log=datos.metadata,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return AuditLogResponse.model_validate(log)


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

