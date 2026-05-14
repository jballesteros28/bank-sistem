from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.enums.wallet_enum import EstadoWallet, TipoWallet
from core.enums import EstadoCuenta, RolUsuario, TipoCuenta
from models.cuenta import Cuenta
from models.usuario import Usuario
from schemas.auth import DatosUsuarioToken
from schemas.wallet_schema import (
    WalletBalanceResponse,
    WalletCreate,
    WalletEstadoUpdate,
    WalletResponse,
    WalletUpdate,
)
from services.cuenta_service import generar_numero_cuenta


def _es_admin(usuario: DatosUsuarioToken) -> bool:
    return usuario.rol in {
        RolUsuario.owner.value,
        RolUsuario.admin.value,
        RolUsuario.SUPER_ADMIN.value,
    }


def _tipo_wallet_a_cuenta(tipo: TipoWallet) -> TipoCuenta:
    """Convierte el enum publico de wallet al enum historico de cuentas."""
    return TipoCuenta(tipo.value)


def _estado_wallet_a_cuenta(estado: EstadoWallet) -> EstadoCuenta:
    """Convierte el estado publico de wallet al enum historico de cuentas."""
    return EstadoCuenta(estado.value)


def _saldo_normalizado(cuenta: Cuenta) -> Decimal:
    return Decimal(cuenta.saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validar_usuario_en_organizacion(
    db: Session,
    *,
    usuario_id: int,
    organizacion_id: UUID,
) -> Usuario:
    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.organizacion_id == organizacion_id,
    ).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la organizacion actual.",
        )
    return usuario


def _resolver_usuario_destino(
    db: Session,
    *,
    datos: WalletCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
) -> int:
    usuario_id = datos.usuario_id or current_user.id
    if not _es_admin(current_user) and usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear wallets para otro usuario.",
        )

    _validar_usuario_en_organizacion(
        db,
        usuario_id=usuario_id,
        organizacion_id=organizacion_id,
    )
    return usuario_id


def _query_wallets_en_organizacion(db: Session, organizacion_id: UUID):
    # Todas las lecturas de wallets se acotan explicitamente al tenant.
    return db.query(Cuenta).filter(Cuenta.organizacion_id == organizacion_id)


def _asegurar_visible(
    cuenta: Cuenta | None,
    *,
    current_user: DatosUsuarioToken,
) -> Cuenta:
    if cuenta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet no encontrada.",
        )
    if not _es_admin(current_user) and cuenta.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet no encontrada.",
        )
    return cuenta


def _asegurar_no_cerrada(cuenta: Cuenta) -> None:
    if cuenta.estado == EstadoCuenta.cerrada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La wallet esta cerrada y no admite operaciones.",
        )


def _asegurar_unica_principal(
    db: Session,
    *,
    usuario_id: int,
    organizacion_id: UUID,
    wallet_id: int | None = None,
) -> None:
    query = db.query(Cuenta).filter(
        Cuenta.usuario_id == usuario_id,
        Cuenta.organizacion_id == organizacion_id,
        Cuenta.es_principal == True,
        Cuenta.estado != EstadoCuenta.cerrada,
    )
    if wallet_id is not None:
        query = query.filter(Cuenta.id != wallet_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene una wallet principal en esta organizacion.",
        )


def crear_wallet(
    datos: WalletCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletResponse:
    """Crea una wallet digital reutilizando Cuenta como persistencia interna."""
    usuario_id = _resolver_usuario_destino(
        db,
        datos=datos,
        current_user=current_user,
        organizacion_id=organizacion_id,
    )

    if datos.es_principal:
        _asegurar_unica_principal(
            db,
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
        )

    nueva_wallet = Cuenta(
        numero=generar_numero_cuenta(db),
        tipo=_tipo_wallet_a_cuenta(datos.tipo),
        alias=datos.alias,
        moneda=datos.moneda,
        saldo=Decimal("0.00"),
        limite_operacion=datos.limite_operacion,
        es_principal=datos.es_principal,
        estado=EstadoCuenta.activa,
        usuario_id=usuario_id,
        organizacion_id=organizacion_id,
    )
    db.add(nueva_wallet)
    db.commit()
    db.refresh(nueva_wallet)
    return WalletResponse.model_validate(nueva_wallet)


def listar_wallets_usuario(
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    usuario_id: int | None = None,
) -> list[WalletResponse]:
    """Lista wallets visibles para el usuario autenticado dentro del tenant."""
    query = _query_wallets_en_organizacion(db, organizacion_id)
    if _es_admin(current_user):
        if usuario_id is not None:
            _validar_usuario_en_organizacion(
                db,
                usuario_id=usuario_id,
                organizacion_id=organizacion_id,
            )
            query = query.filter(Cuenta.usuario_id == usuario_id)
    else:
        query = query.filter(Cuenta.usuario_id == current_user.id)

    wallets = query.order_by(Cuenta.id.asc()).all()
    return [WalletResponse.model_validate(wallet) for wallet in wallets]


def obtener_wallet_por_id(
    wallet_id: int,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletResponse:
    cuenta = _query_wallets_en_organizacion(db, organizacion_id).filter(
        Cuenta.id == wallet_id,
    ).first()
    cuenta = _asegurar_visible(cuenta, current_user=current_user)
    return WalletResponse.model_validate(cuenta)


def obtener_balance_wallet(
    wallet_id: int,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletBalanceResponse:
    cuenta = _query_wallets_en_organizacion(db, organizacion_id).filter(
        Cuenta.id == wallet_id,
    ).first()
    cuenta = _asegurar_visible(cuenta, current_user=current_user)
    return WalletBalanceResponse.model_validate(cuenta)


def actualizar_wallet(
    wallet_id: int,
    datos: WalletUpdate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletResponse:
    cuenta = _query_wallets_en_organizacion(db, organizacion_id).filter(
        Cuenta.id == wallet_id,
    ).first()
    cuenta = _asegurar_visible(cuenta, current_user=current_user)
    _asegurar_no_cerrada(cuenta)

    cambios = datos.model_dump(exclude_unset=True)
    if "es_principal" in cambios and datos.es_principal:
        _asegurar_unica_principal(
            db,
            usuario_id=cuenta.usuario_id,
            organizacion_id=organizacion_id,
            wallet_id=cuenta.id,
        )

    if "alias" in cambios:
        cuenta.alias = datos.alias
    if "tipo" in cambios and datos.tipo is not None:
        cuenta.tipo = _tipo_wallet_a_cuenta(datos.tipo)
    if "moneda" in cambios and datos.moneda is not None:
        cuenta.moneda = datos.moneda
    if "limite_operacion" in cambios:
        cuenta.limite_operacion = datos.limite_operacion
    if "es_principal" in cambios:
        cuenta.es_principal = bool(datos.es_principal)

    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return WalletResponse.model_validate(cuenta)


def cambiar_estado_wallet(
    wallet_id: int,
    datos: WalletEstadoUpdate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletResponse:
    cuenta = _query_wallets_en_organizacion(db, organizacion_id).filter(
        Cuenta.id == wallet_id,
    ).first()
    cuenta = _asegurar_visible(cuenta, current_user=current_user)

    if cuenta.estado == EstadoCuenta.cerrada and datos.estado != EstadoWallet.cerrada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede reabrir una wallet cerrada.",
        )

    cuenta.estado = _estado_wallet_a_cuenta(datos.estado)
    if cuenta.estado == EstadoCuenta.cerrada:
        cuenta.es_principal = False

    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return WalletResponse.model_validate(cuenta)


def cerrar_wallet(
    wallet_id: int,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> WalletResponse:
    cuenta = _query_wallets_en_organizacion(db, organizacion_id).filter(
        Cuenta.id == wallet_id,
    ).first()
    cuenta = _asegurar_visible(cuenta, current_user=current_user)

    saldo = _saldo_normalizado(cuenta)
    if saldo > Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cerrar una wallet con saldo mayor a 0.",
        )

    cuenta.estado = EstadoCuenta.cerrada
    cuenta.es_principal = False
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return WalletResponse.model_validate(cuenta)
