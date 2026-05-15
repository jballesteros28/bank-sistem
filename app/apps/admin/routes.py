from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.apps.admin.schemas import AdminResumenResponse
from app.apps.admin.services import obtener_resumen_admin
from app.apps.auth.dependencies import get_current_admin
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.schemas import OrganizacionResponse
from app.apps.organizaciones.services import listar_organizaciones
from app.apps.usuarios.schemas import UsuarioResponse
from app.apps.usuarios.services import listar_usuarios
from app.apps.wallets.schemas import WalletResponse
from app.apps.wallets.services import listar_wallets
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/resumen", response_model=ApiResponse[AdminResumenResponse])
def get_resumen(
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AdminResumenResponse]:
    return ok(obtener_resumen_admin(current_user, db), "Resumen administrativo obtenido.")


@router.get("/usuarios", response_model=ApiResponse[list[UsuarioResponse]])
def get_admin_usuarios(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[UsuarioResponse]]:
    return ok(listar_usuarios(current_user, db, organizacion_id), "Usuarios administrativos obtenidos.")


@router.get("/wallets", response_model=ApiResponse[list[WalletResponse]])
def get_admin_wallets(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[WalletResponse]]:
    return ok(listar_wallets(current_user, db, organizacion_id=organizacion_id), "Wallets administrativas obtenidas.")


@router.get("/organizaciones", response_model=ApiResponse[list[OrganizacionResponse]])
def get_admin_organizaciones(
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[OrganizacionResponse]]:
    return ok(listar_organizaciones(current_user, db), "Organizaciones administrativas obtenidas.")

