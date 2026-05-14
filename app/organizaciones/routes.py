from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_admin
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

router = APIRouter(prefix="/organizaciones", tags=["Organizaciones"])


@router.post("", response_model=OrganizacionResponse, status_code=status.HTTP_201_CREATED)
def crear_nueva_organizacion(
    datos: OrganizacionCreate,
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_admin),
) -> OrganizacionResponse:
    # Primer endpoint administrativo para dar de alta tenants SaaS.
    return OrganizacionResponse.model_validate(crear_organizacion(datos, db))


@router.get("", response_model=list[OrganizacionResponse], status_code=status.HTTP_200_OK)
def obtener_organizaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_admin),
) -> list[OrganizacionResponse]:
    organizaciones = listar_organizaciones(db, skip=skip, limit=limit)
    return [OrganizacionResponse.model_validate(org) for org in organizaciones]


@router.get("/{organizacion_id}", response_model=OrganizacionResponse, status_code=status.HTTP_200_OK)
def obtener_organizacion(
    organizacion_id: UUID,
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_admin),
) -> OrganizacionResponse:
    return OrganizacionResponse.model_validate(obtener_organizacion_por_id(organizacion_id, db))


@router.patch(
    "/{organizacion_id}/estado",
    response_model=OrganizacionResponse,
    status_code=status.HTTP_200_OK,
)
def actualizar_estado_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionEstadoUpdate,
    db: Session = Depends(get_db),
    _: DatosUsuarioToken = Depends(get_current_admin),
) -> OrganizacionResponse:
    # El cambio de estado queda aislado para futura auditoria y permisos finos.
    organizacion = cambiar_estado_organizacion(organizacion_id, datos.estado, db)
    return OrganizacionResponse.model_validate(organizacion)
