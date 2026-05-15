from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.planes.limit_service import validar_limite_wallets
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.apps.wallets.permissions import ensure_wallet_operation_allowed
from app.apps.wallets.schemas import (
    WalletBalanceResponse,
    WalletCreate,
    WalletEstadoUpdate,
    WalletResponse,
    WalletUpdate,
)
from app.core.permissions import is_admin, is_super_admin
from app.shared.enums import EstadoWallet
from app.shared.utils import normalize_decimal


def _get_user_or_404(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return usuario


def _resolve_create_target(datos: WalletCreate, current_user: DatosUsuarioToken, db: Session) -> tuple[UUID, UUID]:
    usuario_id = datos.usuario_id or current_user.id
    usuario = _get_user_or_404(db, usuario_id)

    requested_org_id = datos.organizacion_id or usuario.organizacion_id
    organizacion_id = resolve_organization_scope(current_user, requested_org_id)
    if organizacion_id is None:
        if usuario.organizacion_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet requiere organizacion.")
        organizacion_id = usuario.organizacion_id

    if usuario.organizacion_id != organizacion_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario fuera de la organizacion.")
    if not is_admin(current_user.rol) and usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear wallets para otro usuario.")

    return usuario_id, organizacion_id


def _ensure_single_primary(
    db: Session,
    usuario_id: UUID,
    organizacion_id: UUID,
    wallet_id: UUID | None = None,
) -> None:
    query = select(Wallet.id).where(
        Wallet.usuario_id == usuario_id,
        Wallet.organizacion_id == organizacion_id,
        Wallet.es_principal.is_(True),
        Wallet.estado != EstadoWallet.cerrada,
    )
    if wallet_id is not None:
        query = query.where(Wallet.id != wallet_id)
    if db.scalar(query) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene una wallet principal.",
        )


def _wallet_query_for_user(current_user: DatosUsuarioToken, organizacion_id: UUID | None = None):
    query = select(Wallet)
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is not None:
        query = query.where(Wallet.organizacion_id == scope_id)
    elif not is_super_admin(current_user.rol):
        query = query.where(Wallet.organizacion_id == current_user.organizacion_id)
    if not is_admin(current_user.rol):
        query = query.where(Wallet.usuario_id == current_user.id)
    return query


def _get_wallet_visible(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> Wallet:
    query = _wallet_query_for_user(current_user).where(Wallet.id == wallet_id)
    wallet = db.scalar(query)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")
    return wallet


def crear_wallet(datos: WalletCreate, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    usuario_id, organizacion_id = _resolve_create_target(datos, current_user, db)
    validar_limite_wallets(db, organizacion_id)
    if datos.es_principal:
        _ensure_single_primary(db, usuario_id, organizacion_id)

    wallet = Wallet(
        alias=datos.alias,
        tipo=datos.tipo,
        moneda=datos.moneda,
        limite_operacion=datos.limite_operacion,
        es_principal=datos.es_principal,
        saldo=Decimal("0.00"),
        estado=EstadoWallet.activa,
        usuario_id=usuario_id,
        organizacion_id=organizacion_id,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def listar_wallets(
    current_user: DatosUsuarioToken,
    db: Session,
    usuario_id: UUID | None = None,
    organizacion_id: UUID | None = None,
) -> list[WalletResponse]:
    query = _wallet_query_for_user(current_user, organizacion_id)
    if usuario_id is not None:
        if not is_admin(current_user.rol) and usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes consultar otro usuario.")
        query = query.where(Wallet.usuario_id == usuario_id)
    wallets = db.scalars(query.order_by(Wallet.id.asc())).all()
    return [WalletResponse.model_validate(wallet) for wallet in wallets]


def obtener_wallet(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    return WalletResponse.model_validate(_get_wallet_visible(wallet_id, current_user, db))


def obtener_balance(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletBalanceResponse:
    return WalletBalanceResponse.model_validate(_get_wallet_visible(wallet_id, current_user, db))


def actualizar_wallet(
    wallet_id: UUID,
    datos: WalletUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WalletResponse:
    wallet = _get_wallet_visible(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    if wallet.estado == EstadoWallet.cerrada:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La wallet esta cerrada.")

    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("es_principal"):
        _ensure_single_primary(db, wallet.usuario_id, wallet.organizacion_id, wallet.id)
    for field, value in cambios.items():
        setattr(wallet, field, value)

    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def cambiar_estado_wallet(
    wallet_id: UUID,
    datos: WalletEstadoUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WalletResponse:
    wallet = _get_wallet_visible(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    wallet.estado = datos.estado
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def cerrar_wallet(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    wallet = _get_wallet_visible(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    if normalize_decimal(wallet.saldo) > Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cerrar una wallet con saldo.")
    wallet.estado = EstadoWallet.cerrada
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)
