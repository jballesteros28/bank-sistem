from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.limit_service import validar_limite_wallets
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.apps.wallets.permissions import ensure_wallet_operation_allowed
from app.apps.wallets.schemas import (
    TIPOS_WALLET_ORGANIZACION,
    TIPOS_WALLET_USUARIO,
    WalletBalanceResponse,
    WalletCreate,
    WalletEstadoUpdate,
    WalletOrganizacionCreate,
    WalletResponse,
    WalletUpdate,
    WalletUsuarioCreate,
)
from app.core.permissions import can_consult_financial_info, is_admin, is_super_admin
from app.shared.enums import EstadoWallet, OwnerTypeWallet
from app.shared.utils import normalize_decimal


def _get_user_or_404(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return usuario


def _get_organization_or_404(db: Session, organizacion_id: UUID) -> Organizacion:
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return organizacion


def _resolve_user_create_target(
    datos: WalletUsuarioCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> tuple[UUID, UUID]:
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

    _get_organization_or_404(db, organizacion_id)
    return usuario_id, organizacion_id


def _resolve_organization_create_target(
    datos: WalletOrganizacionCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> UUID:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")

    requested_org_id = datos.organizacion_id or datos.organizacion_owner_id
    organizacion_id = resolve_organization_scope(current_user, requested_org_id)
    if organizacion_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe indicar una organizacion para crear la wallet.",
        )
    if datos.organizacion_owner_id is not None and datos.organizacion_owner_id != organizacion_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organizacion_owner_id no coincide con la organizacion.",
        )

    _get_organization_or_404(db, organizacion_id)
    return organizacion_id


def _ensure_single_primary(
    db: Session,
    *,
    owner_type: OwnerTypeWallet,
    organizacion_id: UUID,
    usuario_id: UUID | None = None,
    organizacion_owner_id: UUID | None = None,
    wallet_id: UUID | None = None,
) -> None:
    query = select(Wallet.id).where(
        Wallet.owner_type == owner_type,
        Wallet.organizacion_id == organizacion_id,
        Wallet.es_principal.is_(True),
        Wallet.estado != EstadoWallet.cerrada,
    )
    if owner_type == OwnerTypeWallet.usuario:
        if usuario_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet requiere usuario.")
        query = query.where(Wallet.usuario_id == usuario_id)
        detail = "El usuario ya tiene una wallet principal."
    else:
        if organizacion_owner_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet requiere organizacion duena.")
        query = query.where(Wallet.organizacion_owner_id == organizacion_owner_id)
        detail = "La organizacion ya tiene una wallet principal."

    if wallet_id is not None:
        query = query.where(Wallet.id != wallet_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _wallet_query_for_user(current_user: DatosUsuarioToken, organizacion_id: UUID | None = None):
    query = select(Wallet).where(Wallet.owner_type == OwnerTypeWallet.usuario)
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is not None:
        query = query.where(Wallet.organizacion_id == scope_id)
    elif not is_super_admin(current_user.rol):
        query = query.where(Wallet.organizacion_id == current_user.organizacion_id)
    if not is_admin(current_user.rol):
        query = query.where(Wallet.usuario_id == current_user.id)
    return query


def _wallet_query_for_organization(current_user: DatosUsuarioToken, organizacion_id: UUID | None = None):
    if not can_consult_financial_info(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes consultar wallets de organizacion.")

    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar una organizacion.")
    return select(Wallet).where(
        Wallet.owner_type == OwnerTypeWallet.organizacion,
        Wallet.organizacion_id == scope_id,
        Wallet.organizacion_owner_id == scope_id,
    )


def obtener_wallet_por_id(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> Wallet:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")

    if is_super_admin(current_user.rol):
        return wallet

    if wallet.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")

    if wallet.owner_type == OwnerTypeWallet.organizacion:
        if can_consult_financial_info(current_user.rol):
            return wallet
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")

    if is_admin(current_user.rol) or wallet.usuario_id == current_user.id:
        return wallet

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")


def validar_wallet_pertenece_a_organizacion(wallet: Wallet, organizacion_id: UUID) -> None:
    if wallet.organizacion_id != organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")


def _validate_tipo_usuario(datos: WalletUsuarioCreate | WalletUpdate) -> None:
    if datos.tipo is not None and datos.tipo not in TIPOS_WALLET_USUARIO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de wallet no permitido para usuario.")


def _validate_tipo_organizacion(datos: WalletOrganizacionCreate | WalletUpdate) -> None:
    if datos.tipo is not None and datos.tipo not in TIPOS_WALLET_ORGANIZACION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de wallet no permitido para organizacion.",
        )


def crear_wallet_usuario(datos: WalletUsuarioCreate, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    _validate_tipo_usuario(datos)
    usuario_id, organizacion_id = _resolve_user_create_target(datos, current_user, db)
    validar_limite_wallets(db, organizacion_id)
    if datos.es_principal:
        _ensure_single_primary(
            db,
            owner_type=OwnerTypeWallet.usuario,
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
        )

    wallet = Wallet(
        alias=datos.alias,
        tipo=datos.tipo,
        moneda=datos.moneda,
        limite_operacion=datos.limite_operacion,
        es_principal=datos.es_principal,
        saldo=Decimal("0.00"),
        estado=EstadoWallet.activa,
        owner_type=OwnerTypeWallet.usuario,
        usuario_id=usuario_id,
        organizacion_owner_id=None,
        organizacion_id=organizacion_id,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def crear_wallet(datos: WalletCreate, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    return crear_wallet_usuario(datos, current_user, db)


def crear_wallet_organizacion(
    datos: WalletOrganizacionCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WalletResponse:
    _validate_tipo_organizacion(datos)
    organizacion_id = _resolve_organization_create_target(datos, current_user, db)
    validar_limite_wallets(db, organizacion_id)
    if datos.es_principal:
        _ensure_single_primary(
            db,
            owner_type=OwnerTypeWallet.organizacion,
            organizacion_id=organizacion_id,
            organizacion_owner_id=organizacion_id,
        )

    wallet = Wallet(
        alias=datos.alias,
        tipo=datos.tipo,
        moneda=datos.moneda,
        limite_operacion=datos.limite_operacion,
        es_principal=datos.es_principal,
        saldo=Decimal("0.00"),
        estado=EstadoWallet.activa,
        owner_type=OwnerTypeWallet.organizacion,
        usuario_id=None,
        organizacion_owner_id=organizacion_id,
        organizacion_id=organizacion_id,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def listar_wallets_usuario(
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


def listar_wallets(
    current_user: DatosUsuarioToken,
    db: Session,
    usuario_id: UUID | None = None,
    organizacion_id: UUID | None = None,
) -> list[WalletResponse]:
    return listar_wallets_usuario(current_user, db, usuario_id, organizacion_id)


def listar_wallets_organizacion(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[WalletResponse]:
    query = _wallet_query_for_organization(current_user, organizacion_id)
    wallets = db.scalars(query.order_by(Wallet.es_principal.desc(), Wallet.id.asc())).all()
    return [WalletResponse.model_validate(wallet) for wallet in wallets]


def obtener_wallet(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    return WalletResponse.model_validate(obtener_wallet_por_id(wallet_id, current_user, db))


def obtener_balance(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletBalanceResponse:
    return WalletBalanceResponse.model_validate(obtener_wallet_por_id(wallet_id, current_user, db))


def obtener_wallet_principal_organizacion(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> WalletResponse:
    query = _wallet_query_for_organization(current_user, organizacion_id).where(
        Wallet.es_principal.is_(True),
        Wallet.estado != EstadoWallet.cerrada,
    )
    wallet = db.scalar(query.order_by(Wallet.id.asc()))
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet principal de organizacion no encontrada.")
    return WalletResponse.model_validate(wallet)


def actualizar_wallet(
    wallet_id: UUID,
    datos: WalletUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> WalletResponse:
    wallet = obtener_wallet_por_id(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    if wallet.estado == EstadoWallet.cerrada:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La wallet esta cerrada.")

    if wallet.owner_type == OwnerTypeWallet.usuario:
        _validate_tipo_usuario(datos)
    else:
        _validate_tipo_organizacion(datos)

    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("es_principal"):
        _ensure_single_primary(
            db,
            owner_type=wallet.owner_type,
            usuario_id=wallet.usuario_id,
            organizacion_owner_id=wallet.organizacion_owner_id,
            organizacion_id=wallet.organizacion_id,
            wallet_id=wallet.id,
        )
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
    wallet = obtener_wallet_por_id(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    wallet.estado = datos.estado
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


def cerrar_wallet(wallet_id: UUID, current_user: DatosUsuarioToken, db: Session) -> WalletResponse:
    wallet = obtener_wallet_por_id(wallet_id, current_user, db)
    ensure_wallet_operation_allowed(current_user, wallet)
    if normalize_decimal(wallet.saldo) > Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cerrar una wallet con saldo.")
    wallet.estado = EstadoWallet.cerrada
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletResponse.model_validate(wallet)
