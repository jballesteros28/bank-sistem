from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.notificaciones.services import notificar_wallet_congelada, notificar_wallet_creada
from app.apps.wallets.schemas import (
    WalletBalanceResponse,
    WalletCreate,
    WalletEstadoUpdate,
    WalletResponse,
    WalletUpdate,
)
from app.apps.wallets.services import (
    actualizar_wallet,
    cambiar_estado_wallet,
    cerrar_wallet,
    crear_wallet,
    listar_wallets,
    obtener_balance,
    obtener_wallet,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=ApiResponse[WalletResponse], status_code=status.HTTP_201_CREATED)
def post_wallet(
    datos: WalletCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    wallet = crear_wallet(datos, current_user, db)
    notificar_wallet_creada(wallet, db, background_tasks, actor_usuario_id=current_user.id)
    return ok(wallet, "Wallet creada correctamente.")


@router.get("", response_model=ApiResponse[list[WalletResponse]])
def get_wallets(
    usuario_id: UUID | None = Query(default=None),
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[WalletResponse]]:
    return ok(listar_wallets(current_user, db, usuario_id, organizacion_id), "Wallets obtenidas correctamente.")


@router.get("/{wallet_id}", response_model=ApiResponse[WalletResponse])
def get_wallet(
    wallet_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    return ok(obtener_wallet(wallet_id, current_user, db), "Wallet obtenida correctamente.")


@router.get("/{wallet_id}/balance", response_model=ApiResponse[WalletBalanceResponse])
def get_wallet_balance(
    wallet_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletBalanceResponse]:
    return ok(obtener_balance(wallet_id, current_user, db), "Balance obtenido correctamente.")


@router.patch("/{wallet_id}", response_model=ApiResponse[WalletResponse])
def patch_wallet(
    wallet_id: UUID,
    datos: WalletUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    return ok(actualizar_wallet(wallet_id, datos, current_user, db), "Wallet actualizada correctamente.")


@router.patch("/{wallet_id}/estado", response_model=ApiResponse[WalletResponse])
def patch_wallet_estado(
    wallet_id: UUID,
    datos: WalletEstadoUpdate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    wallet = cambiar_estado_wallet(wallet_id, datos, current_user, db)
    notificar_wallet_congelada(wallet, db, background_tasks, actor_usuario_id=current_user.id)
    return ok(wallet, "Estado de wallet actualizado.")


@router.patch("/{wallet_id}/cerrar", response_model=ApiResponse[WalletResponse])
def patch_wallet_cerrar(
    wallet_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    return ok(cerrar_wallet(wallet_id, current_user, db), "Wallet cerrada correctamente.")
