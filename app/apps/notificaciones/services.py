from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.notificaciones.models import Notificacion
from app.apps.notificaciones.schemas import NotificacionCreate, NotificacionResponse
from app.core.permissions import is_admin, is_super_admin
from app.shared.enums import EstadoNotificacion


def crear_notificacion(
    datos: NotificacionCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> NotificacionResponse:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear notificaciones.")

    organizacion_id = datos.organizacion_id or current_user.organizacion_id
    if not is_super_admin(current_user.rol) and organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")

    notificacion = Notificacion(
        usuario_id=datos.usuario_id,
        organizacion_id=organizacion_id,
        tipo=datos.tipo,
        estado=EstadoNotificacion.queued,
        asunto=datos.asunto,
        destinatario=str(datos.destinatario),
        cuerpo=datos.cuerpo,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return NotificacionResponse.model_validate(notificacion)


def listar_notificaciones(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[NotificacionResponse]:
    query = select(Notificacion)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(Notificacion.organizacion_id == organizacion_id)
    elif is_admin(current_user.rol):
        query = query.where(Notificacion.organizacion_id == current_user.organizacion_id)
    else:
        query = query.where(Notificacion.usuario_id == current_user.id)
    notificaciones = db.scalars(query.order_by(Notificacion.fecha_creacion.desc())).all()
    return [NotificacionResponse.model_validate(item) for item in notificaciones]

