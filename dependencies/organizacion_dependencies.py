from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.enums import EstadoOrganizacion
from core.seguridad import get_current_user
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken


async def get_current_organizacion(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organizacion:
    """Resuelve la organizacion activa del usuario autenticado."""
    if current_user.organizacion_id is None:
        # Los usuarios sin tenant asignado no pueden operar datos bancarios.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene una organizacion asignada.",
        )

    organizacion = db.get(Organizacion, current_user.organizacion_id)
    if organizacion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizacion no encontrada.",
        )

    if organizacion.estado != EstadoOrganizacion.activa:
        # Una organizacion inactiva o suspendida queda bloqueada para operar.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La organizacion no esta activa.",
        )

    return organizacion
