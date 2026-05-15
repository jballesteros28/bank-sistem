from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.models import Movimiento
from app.apps.movimientos.permissions import ensure_can_debit_wallet
from app.apps.movimientos.schemas import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
    MovimientoPagoCreate,
    MovimientoResponse,
    MovimientoRetiroCreate,
    MovimientoReversaCreate,
    MovimientoTransferenciaCreate,
)
from app.apps.wallets.models import Wallet
from app.core.permissions import is_admin, is_operator, is_super_admin
from app.shared.enums import EstadoMovimiento, EstadoWallet, TipoMovimiento
from app.shared.utils import normalize_decimal


def _amount(value: Decimal | str | int | float) -> Decimal:
    return normalize_decimal(value)


def _ensure_operator(current_user: DatosUsuarioToken) -> None:
    if not is_operator(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a operadores.")


def _ensure_admin(current_user: DatosUsuarioToken) -> None:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")


def _get_wallet_locked(db: Session, wallet_id: int, label: str) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.id == wallet_id).with_for_update())
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Wallet {label} no encontrada.")
    return wallet


def _ensure_same_organization(wallets: list[Wallet], current_user: DatosUsuarioToken) -> UUID:
    organization_ids = {wallet.organizacion_id for wallet in wallets}
    if len(organization_ids) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    organization_id = organization_ids.pop()
    if not is_super_admin(current_user.rol) and organization_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    return organization_id


def _ensure_active(wallet: Wallet, label: str) -> None:
    if wallet.estado == EstadoWallet.cerrada:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"La wallet {label} esta cerrada.")
    if wallet.estado != EstadoWallet.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"La wallet {label} esta congelada o inactiva.")


def _ensure_same_currency(origen: Wallet, destino: Wallet) -> None:
    if origen.moneda != destino.moneda:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede operar entre monedas distintas.")


def _ensure_limit(wallet: Wallet, amount: Decimal) -> None:
    if wallet.limite_operacion is not None and amount > _amount(wallet.limite_operacion):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El monto supera el limite de operacion.")


def _ensure_balance(wallet: Wallet, amount: Decimal) -> None:
    if _amount(wallet.saldo) < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Saldo insuficiente.")


def _create_movement(
    db: Session,
    *,
    origen: Wallet,
    destino: Wallet,
    amount: Decimal,
    tipo: TipoMovimiento,
    organization_id: UUID,
    descripcion: str | None = None,
    referencia_externa: str | None = None,
    metadata: dict[str, Any] | None = None,
    estado: EstadoMovimiento = EstadoMovimiento.aprobada,
    movimiento_origen_id: int | None = None,
    es_reversa: bool = False,
    motivo_reversa: str | None = None,
) -> Movimiento:
    movimiento = Movimiento(
        wallet_origen_id=origen.id,
        wallet_destino_id=destino.id,
        organizacion_id=organization_id,
        monto=amount,
        tipo=tipo,
        estado=estado,
        descripcion=(descripcion or "").strip() or None,
        referencia_externa=referencia_externa,
        metadata_movimiento=metadata,
        movimiento_origen_id=movimiento_origen_id,
        es_reversa=es_reversa,
        motivo_reversa=motivo_reversa,
    )
    db.add(movimiento)
    return movimiento


def _commit(db: Session, movimiento: Movimiento) -> MovimientoResponse:
    try:
        db.commit()
        db.refresh(movimiento)
    except Exception:
        db.rollback()
        raise
    return MovimientoResponse.model_validate(movimiento)


def crear_deposito(datos: MovimientoDepositoCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    _ensure_operator(current_user)
    amount = _amount(datos.monto)
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([destino], current_user)
    _ensure_active(destino, "destino")

    destino.saldo = _amount(destino.saldo) + amount
    movimiento = _create_movement(
        db,
        origen=destino,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.deposito,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(destino)
    return _commit(db, movimiento)


def crear_retiro(datos: MovimientoRetiroCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    amount = _amount(datos.monto)
    origen = _get_wallet_locked(db, datos.wallet_origen_id, "origen")
    organization_id = _ensure_same_organization([origen], current_user)
    _ensure_active(origen, "origen")
    ensure_can_debit_wallet(current_user, origen)
    _ensure_limit(origen, amount)
    _ensure_balance(origen, amount)

    origen.saldo = _amount(origen.saldo) - amount
    movimiento = _create_movement(
        db,
        origen=origen,
        destino=origen,
        amount=amount,
        tipo=TipoMovimiento.retiro,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(origen)
    return _commit(db, movimiento)


def _crear_entre_wallets(
    datos: MovimientoTransferenciaCreate | MovimientoPagoCreate,
    current_user: DatosUsuarioToken,
    db: Session,
    tipo: TipoMovimiento,
) -> MovimientoResponse:
    amount = _amount(datos.monto)
    origen = _get_wallet_locked(db, datos.wallet_origen_id, "origen")
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    if origen.id == destino.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede operar sobre la misma wallet.")

    organization_id = _ensure_same_organization([origen, destino], current_user)
    _ensure_active(origen, "origen")
    _ensure_active(destino, "destino")
    ensure_can_debit_wallet(current_user, origen)
    _ensure_same_currency(origen, destino)
    _ensure_limit(origen, amount)
    _ensure_balance(origen, amount)

    origen.saldo = _amount(origen.saldo) - amount
    destino.saldo = _amount(destino.saldo) + amount
    movimiento = _create_movement(
        db,
        origen=origen,
        destino=destino,
        amount=amount,
        tipo=tipo,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add_all([origen, destino])
    return _commit(db, movimiento)


def crear_transferencia(
    datos: MovimientoTransferenciaCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    return _crear_entre_wallets(datos, current_user, db, TipoMovimiento.transferencia)


def crear_pago(datos: MovimientoPagoCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    return _crear_entre_wallets(datos, current_user, db, TipoMovimiento.pago)


def crear_cashback(datos: MovimientoCashbackCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    _ensure_operator(current_user)
    amount = _amount(datos.monto)
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([destino], current_user)
    _ensure_active(destino, "destino")

    destino.saldo = _amount(destino.saldo) + amount
    movimiento = _create_movement(
        db,
        origen=destino,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.cashback,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(destino)
    return _commit(db, movimiento)


def crear_ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    _ensure_admin(current_user)
    amount = _amount(datos.monto)
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([destino], current_user)
    _ensure_active(destino, "destino")

    if datos.operacion == "debito":
        _ensure_limit(destino, amount)
        _ensure_balance(destino, amount)
        destino.saldo = _amount(destino.saldo) - amount
    else:
        destino.saldo = _amount(destino.saldo) + amount

    metadata = {**(datos.metadata or {}), "operacion": datos.operacion, "motivo": datos.motivo}
    movimiento = _create_movement(
        db,
        origen=destino,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.ajuste_admin,
        organization_id=organization_id,
        descripcion=datos.descripcion or datos.motivo,
        referencia_externa=datos.referencia_externa,
        metadata=metadata,
    )
    db.add(destino)
    return _commit(db, movimiento)


def _get_reversible_movement(db: Session, movimiento_id: int, current_user: DatosUsuarioToken) -> Movimiento:
    movimiento = db.scalar(select(Movimiento).where(Movimiento.id == movimiento_id).with_for_update())
    if movimiento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if not is_super_admin(current_user.rol) and movimiento.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    if movimiento.es_reversa or movimiento.tipo == TipoMovimiento.reversa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede revertir una reversa.")
    if movimiento.estado == EstadoMovimiento.revertida:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento ya fue revertido.")
    if movimiento.estado != EstadoMovimiento.aprobada:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden revertir movimientos aprobados.")
    return movimiento


def crear_reversa(
    movimiento_id: int,
    datos: MovimientoReversaCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    _ensure_operator(current_user)
    original = _get_reversible_movement(db, movimiento_id, current_user)
    origen = _get_wallet_locked(db, original.wallet_origen_id, "origen")
    destino = _get_wallet_locked(db, original.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([origen, destino], current_user)
    _ensure_active(origen, "origen")
    _ensure_active(destino, "destino")
    if origen.id != destino.id:
        _ensure_same_currency(origen, destino)

    amount = _amount(original.monto)
    reversa_origen = destino
    reversa_destino = origen

    if original.tipo in {TipoMovimiento.deposito, TipoMovimiento.cashback}:
        _ensure_balance(destino, amount)
        destino.saldo = _amount(destino.saldo) - amount
        reversa_origen = destino
        reversa_destino = destino
    elif original.tipo == TipoMovimiento.retiro:
        origen.saldo = _amount(origen.saldo) + amount
        reversa_origen = origen
        reversa_destino = origen
    elif original.tipo == TipoMovimiento.ajuste_admin:
        operation = (original.metadata_movimiento or {}).get("operacion")
        if operation == "debito":
            destino.saldo = _amount(destino.saldo) + amount
        else:
            _ensure_balance(destino, amount)
            destino.saldo = _amount(destino.saldo) - amount
        reversa_origen = destino
        reversa_destino = destino
    elif original.tipo in {TipoMovimiento.transferencia, TipoMovimiento.pago}:
        _ensure_balance(destino, amount)
        destino.saldo = _amount(destino.saldo) - amount
        origen.saldo = _amount(origen.saldo) + amount
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de movimiento no reversible.")

    original.estado = EstadoMovimiento.revertida
    metadata = {**(datos.metadata or {}), "movimiento_original_id": original.id}
    reversa = _create_movement(
        db,
        origen=reversa_origen,
        destino=reversa_destino,
        amount=amount,
        tipo=TipoMovimiento.reversa,
        organization_id=organization_id,
        descripcion=f"Reversa de movimiento {original.id}",
        referencia_externa=datos.referencia_externa or f"reversa:{original.id}",
        metadata=metadata,
        movimiento_origen_id=original.id,
        es_reversa=True,
        motivo_reversa=datos.motivo_reversa,
    )
    db.add_all([original, origen, destino])
    return _commit(db, reversa)


def listar_movimientos(
    current_user: DatosUsuarioToken,
    db: Session,
    skip: int = 0,
    limit: int = 50,
    organizacion_id: UUID | None = None,
) -> list[MovimientoResponse]:
    query = select(Movimiento)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(Movimiento.organizacion_id == organizacion_id)
    else:
        query = query.where(Movimiento.organizacion_id == current_user.organizacion_id)
        if not is_operator(current_user.rol):
            wallets_usuario = select(Wallet.id).where(Wallet.usuario_id == current_user.id)
            query = query.where(
                or_(
                    Movimiento.wallet_origen_id.in_(wallets_usuario),
                    Movimiento.wallet_destino_id.in_(wallets_usuario),
                )
            )
    movimientos = db.scalars(query.order_by(Movimiento.fecha.desc()).offset(skip).limit(limit)).all()
    return [MovimientoResponse.model_validate(movimiento) for movimiento in movimientos]


def obtener_movimiento(
    movimiento_id: int,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    movimiento = db.get(Movimiento, movimiento_id)
    if movimiento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if not is_super_admin(current_user.rol) and movimiento.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if not is_operator(current_user.rol):
        visible = db.scalar(
            select(Wallet.id).where(
                Wallet.usuario_id == current_user.id,
                Wallet.id.in_([movimiento.wallet_origen_id, movimiento.wallet_destino_id]),
            )
        )
        if visible is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    return MovimientoResponse.model_validate(movimiento)

