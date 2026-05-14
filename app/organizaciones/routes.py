from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.enums import RolUsuario
from core.seguridad import get_current_super_admin, get_current_user, is_super_admin
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken
from schemas.organizacion_schema import (
    OrganizacionCreate,
    OrganizacionEstadoUpdate,
    OrganizacionResponse,
)
from services.organizacion_service import (
    cambiar_estado_organizacion,
    crear_organizacion,
    listar_organizaciones,
    obtener_organizacion_por_id,
)
from shared.responses import ApiResponse, ok


router = APIRouter(prefix="/organizaciones", tags=["Organizaciones"])


@router.post("", response_model=ApiResponse[OrganizacionResponse], status_code=status.HTTP_201_CREATED)
def crear_nueva_organizacion(
    datos: OrganizacionCreate,
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_super_admin),
) -> ApiResponse[OrganizacionResponse]:
    """Solo super_admin puede dar de alta organizaciones."""
    organizacion = OrganizacionResponse.model_validate(crear_organizacion(datos, db))
    return ok(organizacion, "Organizacion creada correctamente.")


@router.get("", response_model=ApiResponse[list[OrganizacionResponse]], status_code=status.HTTP_200_OK)
def obtener_organizaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_super_admin),
) -> ApiResponse[list[OrganizacionResponse]]:
    """Solo super_admin puede listar tenants."""
    organizaciones = listar_organizaciones(db, skip=skip, limit=limit)
    data = [OrganizacionResponse.model_validate(org) for org in organizaciones]
    return ok(data, "Organizaciones obtenidas correctamente.")


@router.get("/{organizacion_id}", response_model=ApiResponse[OrganizacionResponse], status_code=status.HTTP_200_OK)
def obtener_organizacion(
    organizacion_id: UUID,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion_actual: Organizacion = Depends(get_current_organizacion),
) -> ApiResponse[OrganizacionResponse]:
    """Super admin ve cualquiera; admin comun solo su propia organizacion."""
    if not is_super_admin(usuario):
        if usuario.rol != RolUsuario.admin.value or organizacion_actual.id != organizacion_id:
            raise HTTPException(status_code=403, detail="Organizacion fuera de alcance.")

    organizacion = OrganizacionResponse.model_validate(obtener_organizacion_por_id(organizacion_id, db))
    return ok(organizacion, "Organizacion obtenida correctamente.")


@router.patch(
    "/{organizacion_id}/estado",
    response_model=ApiResponse[OrganizacionResponse],
    status_code=status.HTTP_200_OK,
)
def actualizar_estado_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionEstadoUpdate,
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_super_admin),
) -> ApiResponse[OrganizacionResponse]:
    """Solo super_admin puede suspender, inactivar o reactivar organizaciones."""
    organizacion = cambiar_estado_organizacion(organizacion_id, datos.estado, db)
    data = OrganizacionResponse.model_validate(organizacion)
    return ok(data, "Estado de organizacion actualizado correctamente.")
