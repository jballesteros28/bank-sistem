from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.enums.movimiento_enum import TipoMovimiento
from core.enums import EstadoCuenta, EstadoTransaccion, RolUsuario, TipoTransaccion
from models.cuenta import Cuenta
from models.log import LogMongo
from models.transaccion import Transaccion
from schemas.auth import DatosUsuarioToken
from schemas.movimiento_schema import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
    MovimientoPagoCreate,
    MovimientoResponse,
    MovimientoRetiroCreate,
    MovimientoReversaCreate,
    MovimientoTransferenciaCreate,
)
from services.log_service import guardar_log


OPERADOR_ROLES = {
    RolUsuario.admin.value,
    RolUsuario.soporte.value,
    RolUsuario.SUPER_ADMIN.value,
    "operator",
}


def _es_operador(usuario: DatosUsuarioToken) -> bool:
    return usuario.rol in OPERADOR_ROLES


def _es_admin_saas(usuario: DatosUsuarioToken) -> bool:
    return usuario.rol in {RolUsuario.admin.value, RolUsuario.SUPER_ADMIN.value}


def _decimal(valor: Decimal | int | float | str) -> Decimal:
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _uuid_movimiento_origen(movimiento_id: int) -> UUID:
    """Genera un UUID estable para enlazar reversas sin cambiar la PK historica."""
    return uuid5(NAMESPACE_URL, f"sistema-bancario:movimiento:{movimiento_id}")


def _agendar_log(
    background_tasks: BackgroundTasks | None,
    *,
    evento: str,
    mensaje: str,
    usuario_id: int,
    metadata: dict[str, Any],
) -> None:
    if background_tasks is None:
        return

    log = LogMongo(
        evento=evento,
        mensaje=mensaje,
        nivel="INFO",
        usuario_id=usuario_id,
        metadata=metadata,
    )
    background_tasks.add_task(guardar_log, log)


def _obtener_wallet_bloqueada(
    db: Session,
    *,
    wallet_id: int,
    organizacion_id: UUID,
    etiqueta: str,
) -> Cuenta:
    wallet = (
        db.query(Cuenta)
        .filter(Cuenta.id == wallet_id)
        .with_for_update()
        .first()
    )
    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet {etiqueta} no encontrada.",
        )
    if wallet.organizacion_id != organizacion_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede operar entre organizaciones.",
        )
    return wallet


def _validar_wallet_activa(wallet: Cuenta, *, etiqueta: str) -> None:
    if wallet.estado == EstadoCuenta.cerrada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La wallet {etiqueta} esta cerrada.",
        )
    if wallet.estado != EstadoCuenta.activa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La wallet {etiqueta} esta congelada o inactiva.",
        )


def _validar_propietario_o_operador(wallet: Cuenta, usuario: DatosUsuarioToken) -> None:
    if _es_operador(usuario):
        return
    if wallet.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La wallet origen no pertenece al usuario autenticado.",
        )


def _validar_misma_moneda(origen: Cuenta, destino: Cuenta) -> None:
    if origen.moneda != destino.moneda:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede operar entre wallets de distinta moneda.",
        )


def _validar_limite(wallet: Cuenta, monto: Decimal) -> None:
    if wallet.limite_operacion is None:
        return

    limite = _decimal(wallet.limite_operacion)
    if monto > limite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto supera el limite de operacion de la wallet.",
        )


def _validar_saldo(wallet: Cuenta, monto: Decimal) -> None:
    if _decimal(wallet.saldo) < monto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente para realizar el movimiento.",
        )


def _registrar_movimiento(
    db: Session,
    *,
    origen: Cuenta,
    destino: Cuenta,
    monto: Decimal,
    tipo: TipoMovimiento,
    descripcion: str | None,
    organizacion_id: UUID,
    referencia_externa: str | None = None,
    metadata: dict[str, Any] | None = None,
    estado: EstadoTransaccion = EstadoTransaccion.aprobada,
    es_reversa: bool = False,
    movimiento_origen_id: UUID | None = None,
    motivo_reversa: str | None = None,
) -> Transaccion:
    movimiento = Transaccion(
        cuenta_origen_id=origen.id,
        cuenta_destino_id=destino.id,
        monto=monto,
        tipo=TipoTransaccion(tipo.value),
        estado=estado,
        fecha=datetime.now(),
        descripcion=(descripcion or "").strip() or None,
        referencia_externa=referencia_externa,
        metadata_movimiento=metadata,
        movimiento_origen_id=movimiento_origen_id,
        es_reversa=es_reversa,
        motivo_reversa=motivo_reversa,
        organizacion_id=organizacion_id,
    )
    db.add(movimiento)
    return movimiento


def _commit_movimiento(db: Session, movimiento: Transaccion) -> MovimientoResponse:
    try:
        db.commit()
        db.refresh(movimiento)
    except Exception:
        db.rollback()
        raise
    return MovimientoResponse.model_validate(movimiento)


def crear_deposito(
    datos: MovimientoDepositoCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    if not _es_operador(current_user):
        raise HTTPException(status_code=403, detail="Solo operadores pueden crear depositos.")

    monto = _decimal(datos.monto)
    destino = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_destino_id,
        organizacion_id=organizacion_id,
        etiqueta="destino",
    )
    _validar_wallet_activa(destino, etiqueta="destino")

    destino.saldo = _decimal(destino.saldo) + monto
    movimiento = _registrar_movimiento(
        db,
        origen=destino,
        destino=destino,
        monto=monto,
        tipo=TipoMovimiento.deposito,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
        organizacion_id=organizacion_id,
    )
    db.add(destino)
    respuesta = _commit_movimiento(db, movimiento)
    _agendar_log(
        background_tasks,
        evento="MovimientoDepositoCreado",
        mensaje=f"Deposito creado en wallet {destino.id}",
        usuario_id=current_user.id,
        metadata={"movimiento_id": respuesta.id, "wallet_destino_id": destino.id, "monto": str(monto)},
    )
    return respuesta


def crear_retiro(
    datos: MovimientoRetiroCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    monto = _decimal(datos.monto)
    origen = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_origen_id,
        organizacion_id=organizacion_id,
        etiqueta="origen",
    )
    _validar_wallet_activa(origen, etiqueta="origen")
    _validar_propietario_o_operador(origen, current_user)
    _validar_limite(origen, monto)
    _validar_saldo(origen, monto)

    origen.saldo = _decimal(origen.saldo) - monto
    movimiento = _registrar_movimiento(
        db,
        origen=origen,
        destino=origen,
        monto=monto,
        tipo=TipoMovimiento.retiro,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
        organizacion_id=organizacion_id,
    )
    db.add(origen)
    respuesta = _commit_movimiento(db, movimiento)
    _agendar_log(
        background_tasks,
        evento="MovimientoRetiroCreado",
        mensaje=f"Retiro creado desde wallet {origen.id}",
        usuario_id=current_user.id,
        metadata={"movimiento_id": respuesta.id, "wallet_origen_id": origen.id, "monto": str(monto)},
    )
    return respuesta


def _crear_movimiento_entre_wallets(
    *,
    datos: MovimientoTransferenciaCreate | MovimientoPagoCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    tipo: TipoMovimiento,
    background_tasks: BackgroundTasks | None,
    estado: EstadoTransaccion = EstadoTransaccion.aprobada,
) -> MovimientoResponse:
    monto = _decimal(datos.monto)
    origen = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_origen_id,
        organizacion_id=organizacion_id,
        etiqueta="origen",
    )
    destino = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_destino_id,
        organizacion_id=organizacion_id,
        etiqueta="destino",
    )
    if origen.id == destino.id:
        raise HTTPException(status_code=400, detail="No se puede operar sobre la misma wallet.")

    _validar_wallet_activa(origen, etiqueta="origen")
    _validar_wallet_activa(destino, etiqueta="destino")
    _validar_propietario_o_operador(origen, current_user)
    _validar_misma_moneda(origen, destino)
    _validar_limite(origen, monto)
    _validar_saldo(origen, monto)

    origen.saldo = _decimal(origen.saldo) - monto
    destino.saldo = _decimal(destino.saldo) + monto
    movimiento = _registrar_movimiento(
        db,
        origen=origen,
        destino=destino,
        monto=monto,
        tipo=tipo,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
        estado=estado,
        organizacion_id=organizacion_id,
    )
    db.add_all([origen, destino])
    respuesta = _commit_movimiento(db, movimiento)
    _agendar_log(
        background_tasks,
        evento=f"Movimiento{tipo.value.title().replace('_', '')}Creado",
        mensaje=f"Movimiento {tipo.value} creado de wallet {origen.id} a {destino.id}",
        usuario_id=current_user.id,
        metadata={
            "movimiento_id": respuesta.id,
            "wallet_origen_id": origen.id,
            "wallet_destino_id": destino.id,
            "monto": str(monto),
        },
    )
    return respuesta


def crear_transferencia(
    datos: MovimientoTransferenciaCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
    estado: EstadoTransaccion = EstadoTransaccion.aprobada,
) -> MovimientoResponse:
    return _crear_movimiento_entre_wallets(
        datos=datos,
        current_user=current_user,
        organizacion_id=organizacion_id,
        db=db,
        tipo=TipoMovimiento.transferencia,
        background_tasks=background_tasks,
        estado=estado,
    )


def crear_pago(
    datos: MovimientoPagoCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    return _crear_movimiento_entre_wallets(
        datos=datos,
        current_user=current_user,
        organizacion_id=organizacion_id,
        db=db,
        tipo=TipoMovimiento.pago,
        background_tasks=background_tasks,
    )


def crear_cashback(
    datos: MovimientoCashbackCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    if not _es_operador(current_user):
        raise HTTPException(status_code=403, detail="Solo operadores pueden crear cashback.")

    monto = _decimal(datos.monto)
    destino = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_destino_id,
        organizacion_id=organizacion_id,
        etiqueta="destino",
    )
    _validar_wallet_activa(destino, etiqueta="destino")

    destino.saldo = _decimal(destino.saldo) + monto
    movimiento = _registrar_movimiento(
        db,
        origen=destino,
        destino=destino,
        monto=monto,
        tipo=TipoMovimiento.cashback,
        descripcion=datos.descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=datos.metadata,
        organizacion_id=organizacion_id,
    )
    db.add(destino)
    respuesta = _commit_movimiento(db, movimiento)
    _agendar_log(
        background_tasks,
        evento="MovimientoCashbackCreado",
        mensaje=f"Cashback creado en wallet {destino.id}",
        usuario_id=current_user.id,
        metadata={"movimiento_id": respuesta.id, "wallet_destino_id": destino.id, "monto": str(monto)},
    )
    return respuesta


def crear_ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    if not _es_admin_saas(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear ajustes.")

    monto = _decimal(datos.monto)
    destino = _obtener_wallet_bloqueada(
        db,
        wallet_id=datos.wallet_destino_id,
        organizacion_id=organizacion_id,
        etiqueta="destino",
    )
    _validar_wallet_activa(destino, etiqueta="destino")

    if datos.operacion == "debito":
        _validar_limite(destino, monto)
        _validar_saldo(destino, monto)
        destino.saldo = _decimal(destino.saldo) - monto
    else:
        destino.saldo = _decimal(destino.saldo) + monto

    metadata = {**(datos.metadata or {}), "operacion": datos.operacion, "motivo": datos.motivo}
    descripcion = datos.descripcion or datos.motivo
    movimiento = _registrar_movimiento(
        db,
        origen=destino,
        destino=destino,
        monto=monto,
        tipo=TipoMovimiento.ajuste_admin,
        descripcion=descripcion,
        referencia_externa=datos.referencia_externa,
        metadata=metadata,
        organizacion_id=organizacion_id,
    )
    db.add(destino)
    respuesta = _commit_movimiento(db, movimiento)
    _agendar_log(
        background_tasks,
        evento="MovimientoAjusteAdminCreado",
        mensaje=f"Ajuste admin {datos.operacion} creado en wallet {destino.id}",
        usuario_id=current_user.id,
        metadata={"movimiento_id": respuesta.id, "wallet_destino_id": destino.id, "monto": str(monto)},
    )
    return respuesta


def _obtener_movimiento_reversible(
    db: Session,
    *,
    movimiento_id: int,
    organizacion_id: UUID,
) -> Transaccion:
    movimiento = (
        db.query(Transaccion)
        .filter(Transaccion.id == movimiento_id)
        .with_for_update()
        .first()
    )
    if movimiento is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    if movimiento.organizacion_id != organizacion_id:
        raise HTTPException(status_code=403, detail="No se puede operar entre organizaciones.")
    if movimiento.es_reversa or movimiento.tipo == TipoTransaccion.reversa:
        raise HTTPException(status_code=400, detail="No se puede revertir una reversa.")
    if movimiento.estado == EstadoTransaccion.revertida:
        raise HTTPException(status_code=400, detail="El movimiento ya fue revertido.")
    if movimiento.estado not in {EstadoTransaccion.aprobada, EstadoTransaccion.completada}:
        raise HTTPException(status_code=400, detail="Solo se pueden revertir movimientos aprobados.")

    reversa_previa = db.query(Transaccion.id).filter(
        Transaccion.organizacion_id == organizacion_id,
        Transaccion.tipo == TipoTransaccion.reversa,
        Transaccion.referencia_externa == f"reversa:{movimiento.id}",
    ).first()
    if reversa_previa is not None:
        raise HTTPException(status_code=400, detail="El movimiento ya fue revertido.")
    return movimiento


def crear_reversa(
    movimiento_id: int,
    datos: MovimientoReversaCreate,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> MovimientoResponse:
    if not _es_operador(current_user):
        raise HTTPException(status_code=403, detail="Solo operadores pueden crear reversas.")

    original = _obtener_movimiento_reversible(
        db,
        movimiento_id=movimiento_id,
        organizacion_id=organizacion_id,
    )
    origen = _obtener_wallet_bloqueada(
        db,
        wallet_id=original.cuenta_origen_id,
        organizacion_id=organizacion_id,
        etiqueta="origen",
    )
    destino = _obtener_wallet_bloqueada(
        db,
        wallet_id=original.cuenta_destino_id,
        organizacion_id=organizacion_id,
        etiqueta="destino",
    )
    _validar_wallet_activa(origen, etiqueta="origen")
    _validar_wallet_activa(destino, etiqueta="destino")
    if origen.id != destino.id:
        _validar_misma_moneda(origen, destino)

    monto = _decimal(original.monto)
    tipo_original = TipoMovimiento(str(getattr(original.tipo, "value", original.tipo)))
    reversa_origen = destino
    reversa_destino = origen

    if tipo_original in {TipoMovimiento.deposito, TipoMovimiento.cashback}:
        _validar_saldo(destino, monto)
        destino.saldo = _decimal(destino.saldo) - monto
        reversa_origen = destino
        reversa_destino = destino
    elif tipo_original == TipoMovimiento.retiro:
        origen.saldo = _decimal(origen.saldo) + monto
        reversa_origen = origen
        reversa_destino = origen
    elif tipo_original == TipoMovimiento.ajuste_admin:
        operacion = (original.metadata_movimiento or {}).get("operacion")
        if operacion == "debito":
            destino.saldo = _decimal(destino.saldo) + monto
        else:
            _validar_saldo(destino, monto)
            destino.saldo = _decimal(destino.saldo) - monto
        reversa_origen = destino
        reversa_destino = destino
    elif tipo_original in {TipoMovimiento.transferencia, TipoMovimiento.pago}:
        _validar_saldo(destino, monto)
        destino.saldo = _decimal(destino.saldo) - monto
        origen.saldo = _decimal(origen.saldo) + monto
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimiento no reversible.")

    original.estado = EstadoTransaccion.revertida
    referencia = datos.referencia_externa or f"reversa:{original.id}"
    metadata = {**(datos.metadata or {}), "movimiento_original_id": original.id}
    reversa = _registrar_movimiento(
        db,
        origen=reversa_origen,
        destino=reversa_destino,
        monto=monto,
        tipo=TipoMovimiento.reversa,
        descripcion=f"Reversa de movimiento {original.id}",
        referencia_externa=referencia,
        metadata=metadata,
        es_reversa=True,
        movimiento_origen_id=_uuid_movimiento_origen(original.id),
        motivo_reversa=datos.motivo_reversa,
        organizacion_id=organizacion_id,
    )
    db.add_all([original, origen, destino])
    respuesta = _commit_movimiento(db, reversa)
    _agendar_log(
        background_tasks,
        evento="MovimientoReversaCreada",
        mensaje=f"Reversa creada para movimiento {original.id}",
        usuario_id=current_user.id,
        metadata={"movimiento_id": respuesta.id, "movimiento_original_id": original.id},
    )
    return respuesta


def listar_movimientos(
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[MovimientoResponse]:
    query = db.query(Transaccion).filter(Transaccion.organizacion_id == organizacion_id)
    if not _es_operador(current_user):
        wallets_usuario = db.query(Cuenta.id).filter(
            Cuenta.usuario_id == current_user.id,
            Cuenta.organizacion_id == organizacion_id,
        ).subquery()
        query = query.filter(
            or_(
                Transaccion.cuenta_origen_id.in_(wallets_usuario),
                Transaccion.cuenta_destino_id.in_(wallets_usuario),
            )
        )

    movimientos = query.order_by(Transaccion.fecha.desc()).offset(skip).limit(limit).all()
    return [MovimientoResponse.model_validate(movimiento) for movimiento in movimientos]


def obtener_movimiento_por_id(
    movimiento_id: int,
    current_user: DatosUsuarioToken,
    organizacion_id: UUID,
    db: Session,
) -> MovimientoResponse:
    movimiento = db.query(Transaccion).filter(
        Transaccion.id == movimiento_id,
        Transaccion.organizacion_id == organizacion_id,
    ).first()
    if movimiento is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

    if not _es_operador(current_user):
        wallet_visible = db.query(Cuenta.id).filter(
            Cuenta.usuario_id == current_user.id,
            Cuenta.organizacion_id == organizacion_id,
            Cuenta.id.in_([movimiento.cuenta_origen_id, movimiento.cuenta_destino_id]),
        ).first()
        if wallet_visible is None:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

    return MovimientoResponse.model_validate(movimiento)
