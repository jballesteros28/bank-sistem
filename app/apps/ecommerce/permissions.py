from fastapi import HTTPException, status

from app.apps.auth.schemas import DatosUsuarioToken
from app.core.permissions import can_consult_financial_info


def ensure_can_read_ecommerce(current_user: DatosUsuarioToken) -> None:
    if can_consult_financial_info(current_user.rol):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes consultar eventos ecommerce.")
