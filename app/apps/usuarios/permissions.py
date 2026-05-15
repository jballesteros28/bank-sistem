from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import is_admin, is_super_admin
from app.shared.enums import RolUsuario


def ensure_can_manage_users(current_user: DatosUsuarioToken) -> None:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes gestionar usuarios.")


def ensure_role_is_assignable(current_user: DatosUsuarioToken, role: RolUsuario) -> None:
    if role == RolUsuario.super_admin and not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo super_admin puede asignar super_admin.")

