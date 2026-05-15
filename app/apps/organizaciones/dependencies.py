from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.models import Organizacion
from app.core.database import get_db
from app.core.permissions import is_super_admin
from app.shared.enums import EstadoOrganizacion


def resolve_organization_scope(
    current_user: DatosUsuarioToken,
    requested_organization_id: UUID | None = None,
) -> UUID | None:
    if is_super_admin(current_user.rol):
        return requested_organization_id

    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")

    if requested_organization_id is not None and requested_organization_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")

    return current_user.organizacion_id


def get_current_organizacion(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organizacion:
    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")

    organizacion = db.get(Organizacion, current_user.organizacion_id)
    if organizacion is None or organizacion.estado != EstadoOrganizacion.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizacion no disponible.")
    return organizacion

