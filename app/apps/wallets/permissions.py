from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.wallets.models import Wallet
from app.core.permissions import is_admin, is_super_admin


def can_operate_wallet(current_user: DatosUsuarioToken, wallet: Wallet) -> bool:
    if is_super_admin(current_user.rol):
        return True
    if is_admin(current_user.rol) and wallet.organizacion_id == current_user.organizacion_id:
        return True
    return wallet.usuario_id == current_user.id


def ensure_wallet_operation_allowed(current_user: DatosUsuarioToken, wallet: Wallet) -> None:
    if not can_operate_wallet(current_user, wallet):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar esta wallet.")

