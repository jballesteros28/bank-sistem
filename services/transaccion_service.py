from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.enums import EstadoTransaccion
from core.excepciones import SaldoInsuficienteError, respuesta_error_estandar
from models.cuenta import Cuenta
from models.log import LogMongo
from models.transaccion import Transaccion
from models.usuario import Usuario
from schemas.auth import DatosUsuarioToken
from schemas.movimiento_schema import MovimientoTransferenciaCreate
from schemas.transaccion import TransaccionCreate, TransaccionOut
from services.log_service import guardar_log
from services.movimiento_service import crear_transferencia


async def manejar_saldo_insuficiente(request: Request, exc: SaldoInsuficienteError):
    """Handler historico para compatibilidad con errores de saldo."""
    correlation_id = getattr(request.state, "correlation_id", None)
    log = LogMongo(
        evento="SaldoInsuficiente",
        mensaje=exc.mensaje,
        nivel="WARNING",
        endpoint=str(request.url),
        ip=request.client.host,
        correlation_id=correlation_id,
    )
    await guardar_log(log)

    return respuesta_error_estandar(
        detalle=exc.mensaje,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="SaldoInsuficiente",
    )


def realizar_transferencia(
    usuario_id: int,
    cuenta_origen_id: int,
    organizacion_id: UUID,
    datos_transaccion: TransaccionCreate,
    db: Session,
    background_tasks: Optional[BackgroundTasks],
    request: Optional[Request] = None,
) -> TransaccionOut:
    """Ejecuta una transferencia legacy usando el motor de movimientos."""
    cuenta_origen_visible = db.query(Cuenta.id).filter(
        Cuenta.id == cuenta_origen_id,
        Cuenta.usuario_id == usuario_id,
        Cuenta.organizacion_id == organizacion_id,
    ).first()
    if cuenta_origen_visible is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta origen no encontrada o no pertenece al usuario.",
        )

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado.")

    usuario_token = DatosUsuarioToken(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol,
        organizacion_id=usuario.organizacion_id,
    )
    movimiento_datos = MovimientoTransferenciaCreate(
        wallet_origen_id=cuenta_origen_id,
        wallet_destino_id=datos_transaccion.cuenta_destino_id,
        monto=datos_transaccion.monto,
        descripcion=datos_transaccion.descripcion,
    )
    movimiento = crear_transferencia(
        movimiento_datos,
        usuario_token,
        organizacion_id,
        db,
        background_tasks,
        estado=EstadoTransaccion.completada,
    )
    transaccion = db.get(Transaccion, movimiento.id)
    if transaccion is None:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la transaccion creada.")
    return TransaccionOut.model_validate(transaccion)


def obtener_historial_usuario(
    usuario_id: int,
    organizacion_id: UUID,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> List[TransaccionOut]:
    """Devuelve historial legacy acotado al usuario y organizacion."""
    cuentas_usuario = db.query(Cuenta.id).filter(
        Cuenta.usuario_id == usuario_id,
        Cuenta.organizacion_id == organizacion_id,
    ).subquery()

    transacciones: List[Transaccion] = (
        db.query(Transaccion)
        .filter(
            Transaccion.organizacion_id == organizacion_id,
            or_(
                Transaccion.cuenta_origen_id.in_(cuentas_usuario),
                Transaccion.cuenta_destino_id.in_(cuentas_usuario),
            ),
        )
        .order_by(Transaccion.fecha.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [TransaccionOut.model_validate(t) for t in transacciones]
