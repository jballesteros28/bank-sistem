from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.wallets.models import Wallet
from app.core.permissions import is_operator


def ensure_can_debit_wallet(current_user: DatosUsuarioToken, wallet: Wallet) -> None:
    if is_operator(current_user.rol):
        return
    if wallet.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La wallet origen no pertenece al usuario.")

