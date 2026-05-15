from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.organizaciones.schemas import OrganizacionBrandingResponse, OrganizacionBrandingUpdate
from app.apps.planes.services import obtener_o_asignar_plan_organizacion
from app.core.permissions import is_admin


def obtener_branding_organizacion(
    organizacion_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> OrganizacionBrandingResponse:
    organizacion = _get_visible_organization(organizacion_id, current_user, db)
    return OrganizacionBrandingResponse.model_validate(organizacion)


def actualizar_branding_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionBrandingUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> OrganizacionBrandingResponse:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes editar branding.")

    organizacion = _get_visible_organization(organizacion_id, current_user, db)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return OrganizacionBrandingResponse.model_validate(organizacion)

    _ensure_unique_branding_fields(db, organizacion.id, cambios)
    _ensure_white_label_allowed(db, organizacion, cambios)

    for field, value in cambios.items():
        setattr(organizacion, field, value)

    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return OrganizacionBrandingResponse.model_validate(organizacion)


def _get_visible_organization(
    organizacion_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> Organizacion:
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        scope_id = organizacion_id
    organizacion = db.get(Organizacion, scope_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return organizacion


def _ensure_unique_branding_fields(
    db: Session,
    organizacion_id: UUID,
    cambios: dict[str, object],
) -> None:
    unique_fields = {
        "subdominio": "Ya existe una organizacion con ese subdominio.",
        "dominio_personalizado": "Ya existe una organizacion con ese dominio personalizado.",
    }
    for field, message in unique_fields.items():
        value = cambios.get(field)
        if value is None:
            continue
        existing_id = db.scalar(
            select(Organizacion.id).where(
                getattr(Organizacion, field) == value,
                Organizacion.id != organizacion_id,
            )
        )
        if existing_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def _ensure_white_label_allowed(
    db: Session,
    organizacion: Organizacion,
    cambios: dict[str, object],
) -> None:
    requires_white_label = cambios.get("permite_white_label_activo") is True or (
        "dominio_personalizado" in cambios and cambios["dominio_personalizado"] is not None
    )
    if not requires_white_label:
        return

    plan = obtener_o_asignar_plan_organizacion(db, organizacion)
    if not plan.permite_white_label:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El plan actual no permite white-label.",
        )
