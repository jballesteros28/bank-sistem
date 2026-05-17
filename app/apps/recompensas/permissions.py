from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import can_consult_financial_info, is_admin
from app.shared.enums import RolUsuario


def ensure_can_manage_rewards(current_user: DatosUsuarioToken) -> None:
    if is_admin(current_user.rol):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")


def ensure_can_apply_rewards(current_user: DatosUsuarioToken) -> None:
    if is_admin(current_user.rol):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")


def ensure_can_read_rewards(current_user: DatosUsuarioToken) -> None:
    if can_consult_financial_info(current_user.rol):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes consultar recompensas.")


def ensure_can_read_own_rewards(current_user: DatosUsuarioToken) -> None:
    if str(current_user.rol) == RolUsuario.cliente.value:
        return
    ensure_can_read_rewards(current_user)
