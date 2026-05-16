from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.apps.auditoria.schemas import AuditLogCreate
from app.apps.auditoria.services import registrar_audit_log
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.models import Movimiento
from app.apps.movimientos.permissions import ensure_can_debit_wallet
from app.apps.movimientos.schemas import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
    MovimientoPagoOrganizacionCreate,
    MovimientoPagoCreate,
    MovimientoResponse,
    MovimientoRetiroCreate,
    MovimientoReversaCreate,
    MovimientoTransferenciaCreate,
)
from app.apps.planes.limit_service import validar_limite_movimientos_mes
from app.apps.wallets.models import Wallet
from app.core.permissions import can_consult_financial_info, is_financial_operator, is_super_admin
from app.shared.enums import EstadoMovimiento, EstadoWallet, MonedaWallet, OwnerTypeWallet, RolUsuario, TipoMovimiento
from app.shared.utils import normalize_decimal


def _amount(value: Decimal | str | int | float) -> Decimal:
    return normalize_decimal(value)


def _json_metadata(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, (UUID, Decimal)):
            cleaned[key] = str(item)
        else:
            cleaned[key] = item
    return cleaned


def _ensure_operator(current_user: DatosUsuarioToken) -> None:
    if not is_financial_operator(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a operadores.")


def _get_wallet_locked(db: Session, wallet_id: UUID, label: str) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.id == wallet_id).with_for_update())
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Wallet {label} no encontrada.")
    return wallet


def _get_wallet_locked_if_present(db: Session, wallet_id: UUID | None, label: str) -> Wallet | None:
    if wallet_id is None:
        return None
    return _get_wallet_locked(db, wallet_id, label)


def _ensure_same_organization(wallets: list[Wallet], current_user: DatosUsuarioToken) -> UUID:
    if not wallets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento debe referenciar una wallet.")
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


def _operation_from_metadata(metadata: dict[str, Any] | None) -> str | None:
    value = (metadata or {}).get("operacion")
    return str(value) if value is not None else None


def _validate_movement_consistency(
    *,
    tipo: TipoMovimiento,
    wallet_origen_id: UUID | None,
    wallet_destino_id: UUID | None,
    operacion: str | None = None,
) -> None:
    if wallet_origen_id is not None and wallet_destino_id is not None and wallet_origen_id == wallet_destino_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede operar sobre la misma wallet.")

    if tipo in {TipoMovimiento.deposito, TipoMovimiento.cashback}:
        if wallet_origen_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento no debe tener wallet origen.")
        if wallet_destino_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento requiere wallet destino.")
        return

    if tipo == TipoMovimiento.retiro:
        if wallet_origen_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento requiere wallet origen.")
        if wallet_destino_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento no debe tener wallet destino.")
        return

    if tipo == TipoMovimiento.ajuste_admin:
        if operacion == "credito":
            if wallet_origen_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El credito no debe tener wallet origen.")
            if wallet_destino_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El credito requiere wallet destino.")
            return
        if operacion == "debito":
            if wallet_origen_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El debito requiere wallet origen.")
            if wallet_destino_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El debito no debe tener wallet destino.")
            return
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operacion de ajuste invalida.")

    if tipo in {TipoMovimiento.transferencia, TipoMovimiento.pago}:
        if wallet_origen_id is None or wallet_destino_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El movimiento requiere wallet origen y destino.",
            )
        return

    if tipo == TipoMovimiento.reversa:
        if wallet_origen_id is None and wallet_destino_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La reversa debe referenciar una wallet.")
        return

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de movimiento invalido.")


def _movement_currency(
    *,
    origen: Wallet | None,
    destino: Wallet | None,
    moneda: MonedaWallet | None = None,
) -> MonedaWallet:
    if moneda is not None:
        return moneda
    if origen is not None and destino is not None:
        _ensure_same_currency(origen, destino)
        return origen.moneda
    wallet = destino or origen
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento debe referenciar una wallet.")
    return wallet.moneda


def _create_movement(
    db: Session,
    *,
    origen: Wallet | None,
    destino: Wallet | None,
    amount: Decimal,
    tipo: TipoMovimiento,
    organization_id: UUID,
    moneda: MonedaWallet | None = None,
    descripcion: str | None = None,
    referencia_externa: str | None = None,
    metadata: dict[str, Any] | None = None,
    estado: EstadoMovimiento = EstadoMovimiento.aprobada,
    movimiento_origen_id: UUID | None = None,
    es_reversa: bool = False,
    motivo_reversa: str | None = None,
) -> Movimiento:
    cleaned_metadata = _json_metadata(metadata)
    _validate_movement_consistency(
        tipo=tipo,
        wallet_origen_id=origen.id if origen is not None else None,
        wallet_destino_id=destino.id if destino is not None else None,
        operacion=_operation_from_metadata(cleaned_metadata),
    )
    if estado == EstadoMovimiento.aprobada:
        validar_limite_movimientos_mes(db, organization_id)
    movimiento = Movimiento(
        wallet_origen_id=origen.id if origen is not None else None,
        wallet_destino_id=destino.id if destino is not None else None,
        organizacion_id=organization_id,
        monto=amount,
        moneda=_movement_currency(origen=origen, destino=destino, moneda=moneda),
        tipo=tipo,
        estado=estado,
        descripcion=(descripcion or "").strip() or None,
        referencia_externa=referencia_externa,
        metadata_movimiento=cleaned_metadata,
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


def _movement_audit_metadata(movimiento: MovimientoResponse) -> dict[str, str]:
    metadata = {
        "movimiento_id": str(movimiento.id),
        "tipo_operacion": movimiento.tipo.value,
        "monto": str(movimiento.monto),
        "moneda": movimiento.moneda.value,
    }
    if movimiento.wallet_origen_id is not None:
        metadata["wallet_origen_id"] = str(movimiento.wallet_origen_id)
    if movimiento.wallet_destino_id is not None:
        metadata["wallet_destino_id"] = str(movimiento.wallet_destino_id)
    operacion = _operation_from_metadata(movimiento.metadata_movimiento)
    if operacion is not None:
        metadata["operacion"] = operacion
    return metadata


def _audit_movimiento(
    movimiento: MovimientoResponse,
    current_user: DatosUsuarioToken,
    db: Session,
    *,
    evento: str = "movimiento_registrado",
    mensaje: str | None = None,
) -> None:
    try:
        registrar_audit_log(
            AuditLogCreate(
                evento=evento,
                mensaje=mensaje or f"Movimiento {movimiento.tipo.value} registrado.",
                actor_usuario_id=current_user.id,
                organizacion_id=movimiento.organizacion_id,
                metadata=_movement_audit_metadata(movimiento),
            ),
            db,
        )
    except Exception:
        db.rollback()


def crear_deposito(datos: MovimientoDepositoCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    _ensure_operator(current_user)
    amount = _amount(datos.monto)
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([destino], current_user)
    _ensure_active(destino, "destino")

    destino.saldo = _amount(destino.saldo) + amount
    movimiento = _create_movement(
        db,
        origen=None,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.deposito,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(destino)
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db)
    return response


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
        destino=None,
        amount=amount,
        tipo=TipoMovimiento.retiro,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(origen)
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db)
    return response


def _crear_entre_wallets(
    datos: MovimientoTransferenciaCreate | MovimientoPagoCreate,
    current_user: DatosUsuarioToken,
    db: Session,
    tipo: TipoMovimiento,
    *,
    metadata_extra: dict[str, Any] | None = None,
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
    metadata = {**(datos.metadata or {}), **(metadata_extra or {})}
    movimiento = _create_movement(
        db,
        origen=origen,
        destino=destino,
        amount=amount,
        tipo=tipo,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=metadata,
    )
    db.add_all([origen, destino])
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db)
    return response


def crear_transferencia(
    datos: MovimientoTransferenciaCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    return _crear_entre_wallets(datos, current_user, db, TipoMovimiento.transferencia)


def crear_pago(datos: MovimientoPagoCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    return _crear_entre_wallets(datos, current_user, db, TipoMovimiento.pago)


def _audit_pago_organizacion(
    movimiento: MovimientoResponse,
    current_user: DatosUsuarioToken,
    db: Session,
) -> None:
    try:
        metadata = {**_movement_audit_metadata(movimiento), "tipo_operacion": "pago_organizacion"}
        registrar_audit_log(
            AuditLogCreate(
                evento="pago_organizacion_realizado",
                mensaje="Pago a organizacion registrado.",
                actor_usuario_id=current_user.id,
                organizacion_id=movimiento.organizacion_id,
                metadata=metadata,
            ),
            db,
        )
    except Exception:
        db.rollback()


def crear_pago_a_organizacion(
    datos: MovimientoPagoOrganizacionCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    if str(current_user.rol) == RolUsuario.soporte.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a operadores.")

    amount = _amount(datos.monto)
    origen = _get_wallet_locked(db, datos.wallet_origen_id, "origen")
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    if origen.id == destino.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede operar sobre la misma wallet.")

    organization_id = _ensure_same_organization([origen, destino], current_user)
    if origen.owner_type != OwnerTypeWallet.usuario or origen.usuario_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet origen debe ser de usuario.")
    if destino.owner_type != OwnerTypeWallet.organizacion or destino.organizacion_owner_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet destino debe ser de organizacion.")

    _ensure_active(origen, "origen")
    _ensure_active(destino, "destino")
    ensure_can_debit_wallet(current_user, origen)
    _ensure_same_currency(origen, destino)
    _ensure_limit(origen, amount)
    _ensure_balance(origen, amount)

    origen.saldo = _amount(origen.saldo) - amount
    destino.saldo = _amount(destino.saldo) + amount
    metadata = {**(datos.metadata or {}), "operacion": "pago_organizacion"}
    movimiento = _create_movement(
        db,
        origen=origen,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.pago,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=metadata,
    )
    db.add_all([origen, destino])
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db, mensaje="Pago registrado.")
    _audit_pago_organizacion(response, current_user, db)
    return response


def crear_cashback(datos: MovimientoCashbackCreate, current_user: DatosUsuarioToken, db: Session) -> MovimientoResponse:
    _ensure_operator(current_user)
    amount = _amount(datos.monto)
    destino = _get_wallet_locked(db, datos.wallet_destino_id, "destino")
    organization_id = _ensure_same_organization([destino], current_user)
    _ensure_active(destino, "destino")

    destino.saldo = _amount(destino.saldo) + amount
    movimiento = _create_movement(
        db,
        origen=None,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.cashback,
        organization_id=organization_id,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
    )
    db.add(destino)
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db)
    return response


def crear_ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    if not is_financial_operator(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a operadores.")
    amount = _amount(datos.monto)
    wallet = _get_wallet_locked(db, datos.wallet_id, "wallet")
    organization_id = _ensure_same_organization([wallet], current_user)
    _ensure_active(wallet, "wallet")

    if datos.operacion == "debito":
        _ensure_limit(wallet, amount)
        _ensure_balance(wallet, amount)
        wallet.saldo = _amount(wallet.saldo) - amount
        origen = wallet
        destino = None
    else:
        wallet.saldo = _amount(wallet.saldo) + amount
        origen = None
        destino = wallet

    metadata = {**(datos.metadata or {}), "operacion": datos.operacion, "motivo": datos.motivo}
    movimiento = _create_movement(
        db,
        origen=origen,
        destino=destino,
        amount=amount,
        tipo=TipoMovimiento.ajuste_admin,
        organization_id=organization_id,
        descripcion=datos.descripcion or datos.motivo,
        referencia_externa=datos.referencia_externa,
        metadata=metadata,
    )
    db.add(wallet)
    response = _commit(db, movimiento)
    _audit_movimiento(response, current_user, db)
    return response


def _get_reversible_movement(db: Session, movimiento_id: UUID, current_user: DatosUsuarioToken) -> Movimiento:
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


def _require_original_wallet(wallet: Wallet | None, label: str) -> Wallet:
    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El movimiento original no tiene wallet {label}.",
        )
    return wallet


def crear_reversa(
    movimiento_id: UUID,
    datos: MovimientoReversaCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    _ensure_operator(current_user)
    original = _get_reversible_movement(db, movimiento_id, current_user)
    original_origen = _get_wallet_locked_if_present(db, original.wallet_origen_id, "origen")
    original_destino = _get_wallet_locked_if_present(db, original.wallet_destino_id, "destino")
    wallets = [wallet for wallet in (original_origen, original_destino) if wallet is not None]
    organization_id = _ensure_same_organization(wallets, current_user)
    for wallet in wallets:
        _ensure_active(wallet, "origen" if wallet.id == original.wallet_origen_id else "destino")
    if original_origen is not None and original_destino is not None:
        _ensure_same_currency(original_origen, original_destino)

    amount = _amount(original.monto)
    reversa_origen: Wallet | None = None
    reversa_destino: Wallet | None = None

    if original.tipo in {TipoMovimiento.deposito, TipoMovimiento.cashback}:
        destino = _require_original_wallet(original_destino, "destino")
        _ensure_balance(destino, amount)
        destino.saldo = _amount(destino.saldo) - amount
        reversa_origen = destino
    elif original.tipo == TipoMovimiento.retiro:
        origen = _require_original_wallet(original_origen, "origen")
        origen.saldo = _amount(origen.saldo) + amount
        reversa_destino = origen
    elif original.tipo == TipoMovimiento.ajuste_admin:
        operation = _operation_from_metadata(original.metadata_movimiento)
        if operation == "credito":
            destino = _require_original_wallet(original_destino, "destino")
            _ensure_balance(destino, amount)
            destino.saldo = _amount(destino.saldo) - amount
            reversa_origen = destino
        elif operation == "debito":
            origen = _require_original_wallet(original_origen, "origen")
            origen.saldo = _amount(origen.saldo) + amount
            reversa_destino = origen
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operacion de ajuste original invalida.")
    elif original.tipo in {TipoMovimiento.transferencia, TipoMovimiento.pago}:
        origen = _require_original_wallet(original_origen, "origen")
        destino = _require_original_wallet(original_destino, "destino")
        _ensure_balance(destino, amount)
        destino.saldo = _amount(destino.saldo) - amount
        origen.saldo = _amount(origen.saldo) + amount
        reversa_origen = destino
        reversa_destino = origen
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de movimiento no reversible.")

    original.estado = EstadoMovimiento.revertida
    metadata = {
        **(datos.metadata or {}),
        "movimiento_original_id": str(original.id),
        "tipo_original": original.tipo.value,
    }
    reversa = _create_movement(
        db,
        origen=reversa_origen,
        destino=reversa_destino,
        amount=amount,
        moneda=original.moneda,
        tipo=TipoMovimiento.reversa,
        organization_id=organization_id,
        descripcion=f"Reversa de movimiento {original.id}",
        referencia_externa=datos.referencia_externa or f"reversa:{original.id}",
        metadata=metadata,
        movimiento_origen_id=original.id,
        es_reversa=True,
        motivo_reversa=datos.motivo_reversa,
    )
    db.add(original)
    for wallet in wallets:
        db.add(wallet)
    response = _commit(db, reversa)
    _audit_movimiento(response, current_user, db, evento="movimiento_revertido", mensaje="Reversa registrada.")
    return response


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
        if not can_consult_financial_info(current_user.rol):
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
    movimiento_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> MovimientoResponse:
    movimiento = db.get(Movimiento, movimiento_id)
    if movimiento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if not is_super_admin(current_user.rol) and movimiento.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if not can_consult_financial_info(current_user.rol):
        wallet_ids = [
            wallet_id
            for wallet_id in (movimiento.wallet_origen_id, movimiento.wallet_destino_id)
            if wallet_id is not None
        ]
        visible = db.scalar(
            select(Wallet.id).where(
                Wallet.usuario_id == current_user.id,
                Wallet.id.in_(wallet_ids),
            )
        )
        if visible is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    return MovimientoResponse.model_validate(movimiento)
