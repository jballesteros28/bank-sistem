from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.organizaciones.schemas import OrganizacionResponse, OrganizacionUpdate
from app.core.permissions import is_super_admin


def listar_organizaciones(current_user: DatosUsuarioToken, db: Session) -> list[OrganizacionResponse]:
    query = select(Organizacion).order_by(Organizacion.fecha_creacion.desc())
    if not is_super_admin(current_user.rol):
        query = query.where(Organizacion.id == current_user.organizacion_id)
    return [OrganizacionResponse.model_validate(org) for org in db.scalars(query).all()]


def obtener_organizacion(
    organizacion_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> OrganizacionResponse:
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        scope_id = organizacion_id
    organizacion = db.get(Organizacion, scope_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return OrganizacionResponse.model_validate(organizacion)


def actualizar_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> OrganizacionResponse:
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        scope_id = organizacion_id
    organizacion = db.get(Organizacion, scope_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")

    cambios = datos.model_dump(exclude_unset=True)
    if "estado" in cambios and not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo super_admin puede cambiar estado.")

    for field, value in cambios.items():
        setattr(organizacion, field, value)

    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return OrganizacionResponse.model_validate(organizacion)

