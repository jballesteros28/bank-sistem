from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.notificaciones.services import notificar_organizacion_suspendida
from app.apps.organizaciones.branding_service import (
    actualizar_branding_organizacion,
    obtener_branding_organizacion,
)
from app.apps.organizaciones.schemas import (
    OrganizacionBrandingResponse,
    OrganizacionBrandingUpdate,
    OrganizacionResponse,
    OrganizacionUpdate,
)
from app.apps.organizaciones.services import (
    actualizar_organizacion,
    listar_organizaciones,
    obtener_organizacion,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/organizaciones", tags=["Organizaciones"])


@router.get("", response_model=ApiResponse[list[OrganizacionResponse]])
def list_organizaciones(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[OrganizacionResponse]]:
    return ok(listar_organizaciones(current_user, db), "Organizaciones obtenidas correctamente.")


@router.get("/me", response_model=ApiResponse[OrganizacionResponse])
def my_organization(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionResponse]:
    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")
    return ok(obtener_organizacion(current_user.organizacion_id, current_user, db), "Organizacion actual obtenida.")


@router.get("/me/branding", response_model=ApiResponse[OrganizacionBrandingResponse])
def my_organization_branding(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionBrandingResponse]:
    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")
    return ok(
        obtener_branding_organizacion(current_user.organizacion_id, current_user, db),
        "Branding de organizacion obtenido correctamente.",
    )


@router.patch("/me/branding", response_model=ApiResponse[OrganizacionBrandingResponse])
def patch_my_organization_branding(
    datos: OrganizacionBrandingUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionBrandingResponse]:
    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")
    return ok(
        actualizar_branding_organizacion(current_user.organizacion_id, datos, current_user, db),
        "Branding de organizacion actualizado correctamente.",
    )


@router.get("/{organizacion_id}/branding", response_model=ApiResponse[OrganizacionBrandingResponse])
def get_organization_branding(
    organizacion_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionBrandingResponse]:
    return ok(
        obtener_branding_organizacion(organizacion_id, current_user, db),
        "Branding de organizacion obtenido correctamente.",
    )


@router.patch("/{organizacion_id}/branding", response_model=ApiResponse[OrganizacionBrandingResponse])
def patch_organization_branding(
    organizacion_id: UUID,
    datos: OrganizacionBrandingUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionBrandingResponse]:
    return ok(
        actualizar_branding_organizacion(organizacion_id, datos, current_user, db),
        "Branding de organizacion actualizado correctamente.",
    )


@router.get("/{organizacion_id}", response_model=ApiResponse[OrganizacionResponse])
def get_organizacion(
    organizacion_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionResponse]:
    return ok(obtener_organizacion(organizacion_id, current_user, db), "Organizacion obtenida correctamente.")


@router.patch("/{organizacion_id}", response_model=ApiResponse[OrganizacionResponse])
def patch_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionUpdate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrganizacionResponse]:
    organizacion = actualizar_organizacion(organizacion_id, datos, current_user, db)
    notificar_organizacion_suspendida(organizacion.id, db, background_tasks, actor_usuario_id=current_user.id)
    return ok(organizacion, "Organizacion actualizada correctamente.")
