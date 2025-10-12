from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status, Request, BackgroundTasks
from datetime import datetime
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP

from models.transaccion import Transaccion
from models.cuenta import Cuenta
from models.usuario import Usuario
from schemas.transaccion import TransaccionCreate, TransaccionOut
from core.enums import EstadoCuenta
from core.excepciones import SaldoInsuficienteError, respuesta_error_estandar
from services.log_service import guardar_log
from models.log import LogMongo

# 📧 Enviadores especializados
from services.enviadores_email.transferencia_exitosa import enviar_email_transferencia_exitosa
from services.enviadores_email.transferencia_recibida import enviar_email_transferencia_recibida


# ==========================================================
# ⚠️ Handler de excepción personalizada
# ==========================================================
async def manejar_saldo_insuficiente(request: Request, exc: SaldoInsuficienteError):
    """
    Se ejecuta automáticamente cuando se lanza un SaldoInsuficienteError.
    Guarda log en Mongo y devuelve respuesta estándar.
    """
    correlation_id = getattr(request.state, "correlation_id", None)
    log = LogMongo(
        evento="SaldoInsuficiente",
        mensaje=exc.mensaje,
        nivel="WARNING",
        endpoint=str(request.url),
        ip=request.client.host,
        correlation_id=correlation_id
    )
    await guardar_log(log)

    return respuesta_error_estandar(
        detalle=exc.mensaje,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="SaldoInsuficiente",
    )


# ==========================================================
# 💳 Ejecutar transferencia entre cuentas
# ==========================================================
def realizar_transferencia(
    usuario_id: int,
    cuenta_origen_id: int,
    datos_transaccion: TransaccionCreate,
    db: Session,
    background_tasks: Optional[BackgroundTasks],
    request: Optional[Request] = None
) -> TransaccionOut:
    """
    Ejecuta una transferencia entre cuentas con seguridad:
    - Bloquea cuentas origen y destino (FOR UPDATE).
    - Valida estados, saldos y montos.
    - Registra la transacción y actualiza balances.
    - Dispara logs y notificaciones.
    """
    correlation_id = getattr(request.state, "correlation_id", None) if request else None

    # 🔍 1. Obtener y bloquear cuenta origen
    cuenta_origen: Optional[Cuenta] = (
        db.query(Cuenta)
        .filter(Cuenta.id == cuenta_origen_id, Cuenta.usuario_id == usuario_id)
        .with_for_update()
        .first()
    )

    if not cuenta_origen:
        if background_tasks:
            log = LogMongo(
                evento="TransferenciaFallida",
                mensaje=f"Cuenta origen {cuenta_origen_id} no encontrada para usuario {usuario_id}",
                nivel="WARNING",
                usuario_id=usuario_id,
                metadata={"cuenta_origen": cuenta_origen_id},
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta origen no encontrada o no pertenece al usuario.",
        )

    # 🔍 2. Obtener y bloquear cuenta destino
    cuenta_destino: Optional[Cuenta] = (
        db.query(Cuenta)
        .filter(Cuenta.id == datos_transaccion.cuenta_destino_id)
        .with_for_update()
        .first()
    )

    if not cuenta_destino:
        if background_tasks:
            log = LogMongo(
                evento="TransferenciaFallida",
                mensaje=f"Cuenta destino {datos_transaccion.cuenta_destino_id} no encontrada",
                nivel="WARNING",
                usuario_id=usuario_id,
                metadata={"cuenta_destino": datos_transaccion.cuenta_destino_id},
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta destino no encontrada.",
        )

    if cuenta_origen.id == cuenta_destino.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede transferir dinero a la misma cuenta."
        )

    # ❄️ 3. Validar estados
    if cuenta_origen.estado != EstadoCuenta.activa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta origen está congelada o inactiva.",
        )
    if cuenta_destino.estado != EstadoCuenta.activa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta destino está congelada o inactiva.",
        )

    # 💰 4. Normalizar montos
    monto_transferencia: Decimal = Decimal(datos_transaccion.monto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    saldo_origen: Decimal = Decimal(cuenta_origen.saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ⛔ Validar monto positivo
    if monto_transferencia <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto debe ser mayor a cero.",
        )

    # 💸 5. Validar saldo suficiente
    if saldo_origen < monto_transferencia:
        if background_tasks:
            log = LogMongo(
                evento="TransferenciaSaldoInsuficiente",
                mensaje=f"Saldo insuficiente en cuenta {cuenta_origen.id}, usuario {usuario_id}",
                nivel="WARNING",
                usuario_id=usuario_id,
                metadata={
                    "cuenta_origen": cuenta_origen.id,
                    "saldo_actual": str(saldo_origen),
                    "monto_intentado": str(monto_transferencia),
                },
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)
        raise SaldoInsuficienteError("El saldo de la cuenta origen no es suficiente.")

    # 🧾 6. Registrar transacción
    nueva_transaccion = Transaccion(
        cuenta_origen_id=cuenta_origen.id,
        cuenta_destino_id=cuenta_destino.id,
        monto=monto_transferencia,
        tipo=datos_transaccion.tipo,
        estado="completada",
        fecha=datetime.now(),
        descripcion=(datos_transaccion.descripcion or "").strip(),
    )

    # 💳 7. Actualizar saldos
    cuenta_origen.saldo = (saldo_origen - monto_transferencia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cuenta_destino.saldo = (Decimal(cuenta_destino.saldo) + monto_transferencia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 💾 8. Guardar cambios
    db.add_all([nueva_transaccion, cuenta_origen, cuenta_destino])
    db.commit()
    db.refresh(nueva_transaccion)

    # ==========================================================
    # 🧠 9. Logs y notificaciones
    # ==========================================================
    if background_tasks:
        # Log de éxito
        log_exito = LogMongo(
            evento="TransferenciaExitosa",
            mensaje=f"Se transfirieron ${monto_transferencia} de cuenta {cuenta_origen.id} a {cuenta_destino.id}",
            nivel="INFO",
            usuario_id=usuario_id,
            metadata={
                "origen": cuenta_origen.id,
                "destino": cuenta_destino.id,
                "monto": str(monto_transferencia),
                "transaccion_id": nueva_transaccion.id,
            },
            correlation_id=correlation_id
        )
        background_tasks.add_task(guardar_log, log_exito)

        # 📧 Emisor
        emisor: Optional[Usuario] = db.get(Usuario, usuario_id)
        if emisor and emisor.email:
            try:
                background_tasks.add_task(
                    enviar_email_transferencia_exitosa,
                    email=emisor.email,
                    nombre=emisor.nombre,
                    id_transaccion=nueva_transaccion.id,
                    monto=nueva_transaccion.monto,
                    cuenta_origen=cuenta_origen.id,
                    cuenta_destino=cuenta_destino.id,
                    fecha=nueva_transaccion.fecha.strftime("%Y-%m-%d %H:%M"),
                    descripcion=nueva_transaccion.descripcion,
                )
            except Exception as e:
                log_error_emisor = LogMongo(
                    evento="ErrorNotificacionEmisor",
                    mensaje=f"No se pudo enviar mail al emisor {emisor.email}: {str(e)}",
                    nivel="ERROR",
                    usuario_id=usuario_id,
                    metadata={"transaccion_id": nueva_transaccion.id},
                    correlation_id=correlation_id
                )
                background_tasks.add_task(guardar_log, log_error_emisor)

        # 📧 Receptor
        receptor: Optional[Usuario] = db.get(Usuario, cuenta_destino.usuario_id)
        if receptor and receptor.email:
            try:
                background_tasks.add_task(
                    enviar_email_transferencia_recibida,
                    email=receptor.email,
                    nombre=receptor.nombre,
                    id_transaccion=nueva_transaccion.id,
                    monto=nueva_transaccion.monto,
                    cuenta_origen=cuenta_origen.id,
                    cuenta_destino=cuenta_destino.id,
                    fecha=nueva_transaccion.fecha.strftime("%Y-%m-%d %H:%M"),
                    descripcion=nueva_transaccion.descripcion,
                )
            except Exception as e:
                log_error_receptor = LogMongo(
                    evento="ErrorNotificacionReceptor",
                    mensaje=f"No se pudo enviar mail al receptor {receptor.email}: {str(e)}",
                    nivel="ERROR",
                    usuario_id=receptor.id,
                    metadata={"transaccion_id": nueva_transaccion.id},
                    correlation_id=correlation_id
                )
                background_tasks.add_task(guardar_log, log_error_receptor)

    # 📤 10. Respuesta al cliente
    return TransaccionOut.model_validate(nueva_transaccion)


# ==========================================================
# 📄 Historial de transacciones de un usuario
# ==========================================================
def obtener_historial_usuario(
    usuario_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> List[TransaccionOut]:
    """
    Devuelve historial de transacciones de un usuario:
    - Incluye transacciones como origen o destino.
    - Ordenadas por fecha descendente.
    - Permite paginación opcional.
    """
    cuentas_usuario = db.query(Cuenta.id).filter(Cuenta.usuario_id == usuario_id).subquery()

    transacciones: List[Transaccion] = (
        db.query(Transaccion)
        .filter(
            or_(
                Transaccion.cuenta_origen_id.in_(cuentas_usuario),
                Transaccion.cuenta_destino_id.in_(cuentas_usuario),
            )
        )
        .order_by(Transaccion.fecha.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [TransaccionOut.model_validate(t) for t in transacciones]

