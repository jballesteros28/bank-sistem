from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_user
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken
from schemas.wallet_schema import (
    WalletBalanceResponse,
    WalletCreate,
    WalletEstadoUpdate,
    WalletResponse,
    WalletUpdate,
)
from services.wallet_service import (
    actualizar_wallet,
    cambiar_estado_wallet,
    cerrar_wallet,
    crear_wallet,
    listar_wallets_usuario,
    obtener_balance_wallet,
    obtener_wallet_por_id,
)
from shared.responses import ApiResponse, ok


router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=ApiResponse[WalletResponse], status_code=status.HTTP_201_CREATED)
def crear_nueva_wallet(
    datos: WalletCreate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    """Crea una wallet SaaS dentro de la organizacion autenticada."""
    wallet = crear_wallet(datos, usuario, organizacion.id, db)
    return ok(wallet, "Wallet creada correctamente.")


@router.get("", response_model=ApiResponse[list[WalletResponse]], status_code=status.HTTP_200_OK)
def listar_wallets(
    usuario_id: int | None = Query(default=None, gt=0),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[list[WalletResponse]]:
    """Lista wallets visibles para el usuario y tenant actual."""
    wallets = listar_wallets_usuario(usuario, organizacion.id, db, usuario_id=usuario_id)
    return ok(wallets, "Wallets obtenidas correctamente.")


@router.get("/{wallet_id}", response_model=ApiResponse[WalletResponse], status_code=status.HTTP_200_OK)
def obtener_wallet(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    """Obtiene una wallet por id respetando el aislamiento por organizacion."""
    wallet = obtener_wallet_por_id(wallet_id, usuario, organizacion.id, db)
    return ok(wallet, "Wallet obtenida correctamente.")


@router.get("/{wallet_id}/balance", response_model=ApiResponse[WalletBalanceResponse])
def obtener_balance(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletBalanceResponse]:
    """Devuelve el saldo actual de una wallet visible."""
    balance = obtener_balance_wallet(wallet_id, usuario, organizacion.id, db)
    return ok(balance, "Balance obtenido correctamente.")


@router.patch("/{wallet_id}", response_model=ApiResponse[WalletResponse])
def actualizar_datos_wallet(
    wallet_id: int,
    datos: WalletUpdate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    """Actualiza metadatos de la wallet sin modificar saldo."""
    wallet = actualizar_wallet(wallet_id, datos, usuario, organizacion.id, db)
    return ok(wallet, "Wallet actualizada correctamente.")


@router.patch("/{wallet_id}/estado", response_model=ApiResponse[WalletResponse])
def cambiar_estado(
    wallet_id: int,
    datos: WalletEstadoUpdate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    """Cambia el estado operativo de una wallet."""
    wallet = cambiar_estado_wallet(wallet_id, datos, usuario, organizacion.id, db)
    return ok(wallet, "Estado de wallet actualizado correctamente.")


@router.patch("/{wallet_id}/cerrar", response_model=ApiResponse[WalletResponse])
def cerrar(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    """Cierra una wallet solo si no conserva saldo."""
    wallet = cerrar_wallet(wallet_id, usuario, organizacion.id, db)
    return ok(wallet, "Wallet cerrada correctamente.")
