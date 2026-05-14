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


router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def crear_nueva_wallet(
    datos: WalletCreate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """Crea una wallet SaaS dentro de la organizacion autenticada."""
    return crear_wallet(datos, usuario, organizacion.id, db)


@router.get("", response_model=list[WalletResponse], status_code=status.HTTP_200_OK)
def listar_wallets(
    usuario_id: int | None = Query(default=None, gt=0),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> list[WalletResponse]:
    """Lista wallets visibles para el usuario y tenant actual."""
    return listar_wallets_usuario(usuario, organizacion.id, db, usuario_id=usuario_id)


@router.get("/{wallet_id}", response_model=WalletResponse, status_code=status.HTTP_200_OK)
def obtener_wallet(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """Obtiene una wallet por id respetando el aislamiento por organizacion."""
    return obtener_wallet_por_id(wallet_id, usuario, organizacion.id, db)


@router.get("/{wallet_id}/balance", response_model=WalletBalanceResponse)
def obtener_balance(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletBalanceResponse:
    """Devuelve el saldo actual de una wallet visible."""
    return obtener_balance_wallet(wallet_id, usuario, organizacion.id, db)


@router.patch("/{wallet_id}", response_model=WalletResponse)
def actualizar_datos_wallet(
    wallet_id: int,
    datos: WalletUpdate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """Actualiza metadatos de la wallet sin modificar saldo."""
    return actualizar_wallet(wallet_id, datos, usuario, organizacion.id, db)


@router.patch("/{wallet_id}/estado", response_model=WalletResponse)
def cambiar_estado(
    wallet_id: int,
    datos: WalletEstadoUpdate,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """Cambia el estado operativo de una wallet."""
    return cambiar_estado_wallet(wallet_id, datos, usuario, organizacion.id, db)


@router.patch("/{wallet_id}/cerrar", response_model=WalletResponse)
def cerrar(
    wallet_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """Cierra una wallet solo si no conserva saldo."""
    return cerrar_wallet(wallet_id, usuario, organizacion.id, db)

