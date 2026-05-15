from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import is_admin, is_super_admin


def ensure_can_manage_plans(current_user: DatosUsuarioToken) -> None:
    if not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo super_admin puede gestionar planes.")


def ensure_can_view_current_plan(current_user: DatosUsuarioToken) -> None:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a administradores.")
