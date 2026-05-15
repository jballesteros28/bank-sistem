from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.notificaciones.schemas import NotificacionCreate, NotificacionResponse
from app.apps.notificaciones.services import crear_notificacion, listar_notificaciones
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("", response_model=ApiResponse[list[NotificacionResponse]])
def get_notificaciones(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[NotificacionResponse]]:
    return ok(listar_notificaciones(current_user, db, organizacion_id), "Notificaciones obtenidas.")


@router.post("", response_model=ApiResponse[NotificacionResponse], status_code=status.HTTP_201_CREATED)
def post_notificacion(
    datos: NotificacionCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[NotificacionResponse]:
    return ok(crear_notificacion(datos, current_user, db), "Notificacion creada.")

