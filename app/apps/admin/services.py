from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.apps.admin.schemas import AdminResumenResponse
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.models import Movimiento
from app.apps.organizaciones.models import Organizacion
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.core.permissions import is_super_admin


def _count(db: Session, model: type, organization_field: object | None, organization_id: object | None) -> int:
    query = select(func.count()).select_from(model)
    if organization_field is not None and organization_id is not None:
        query = query.where(organization_field == organization_id)
    return int(db.scalar(query) or 0)


def obtener_resumen_admin(current_user: DatosUsuarioToken, db: Session) -> AdminResumenResponse:
    organization_id = None if is_super_admin(current_user.rol) else current_user.organizacion_id
    return AdminResumenResponse(
        organizaciones=_count(db, Organizacion, Organizacion.id, organization_id),
        usuarios=_count(db, Usuario, Usuario.organizacion_id, organization_id),
        wallets=_count(db, Wallet, Wallet.organizacion_id, organization_id),
        movimientos=_count(db, Movimiento, Movimiento.organizacion_id, organization_id),
    )

