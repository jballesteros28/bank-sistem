from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.notificaciones.schemas import (
    NotificacionListResponse,
    NotificacionMarcarLeidaRequest,
    NotificacionResponse,
)
from app.apps.notificaciones.services import (
    contar_no_leidas,
    listar_notificaciones_organizacion,
    listar_notificaciones_usuario,
    marcar_como_leida,
    marcar_todas_como_leidas,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("", response_model=ApiResponse[NotificacionListResponse])
def get_notificaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[NotificacionListResponse]:
    return ok(
        listar_notificaciones_usuario(current_user, db, organizacion_id, skip, limit),
        "Notificaciones obtenidas.",
    )


@router.get("/no-leidas/count", response_model=ApiResponse[int])
def get_notificaciones_no_leidas_count(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[int]:
    return ok(contar_no_leidas(current_user, db), "Cantidad de notificaciones no leidas obtenida.")


@router.get("/organizacion", response_model=ApiResponse[NotificacionListResponse])
def get_notificaciones_organizacion(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[NotificacionListResponse]:
    return ok(
        listar_notificaciones_organizacion(current_user, db, organizacion_id, skip, limit),
        "Notificaciones de organizacion obtenidas.",
    )


@router.patch("/{notificacion_id}/leida", response_model=ApiResponse[NotificacionResponse])
def patch_notificacion_leida(
    notificacion_id: UUID,
    datos: NotificacionMarcarLeidaRequest = Body(default_factory=NotificacionMarcarLeidaRequest),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[NotificacionResponse]:
    return ok(
        marcar_como_leida(notificacion_id, datos, current_user, db),
        "Notificacion actualizada.",
    )


@router.patch("/marcar-todas-leidas", response_model=ApiResponse[int])
def patch_notificaciones_marcar_todas_leidas(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[int]:
    return ok(marcar_todas_como_leidas(current_user, db), "Notificaciones marcadas como leidas.")
