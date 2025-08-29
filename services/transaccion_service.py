from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.transaccion import Transaccion
from models.cuenta import Cuenta
from schemas.transaccion import TransaccionCreate, TransaccionOut
from fastapi import HTTPException, status, Request
from core.enums import EstadoCuenta
from core.excepciones import SaldoInsuficienteError, CuentaCongeladaError, respuesta_error_estandar
from services.log_service import guardar_log
from models.log import LogMongo
from datetime import datetime
from typing import List



# 🔒 Manejo de errores de saldo insuficiente
async def manejar_saldo_insuficiente(request: Request, exc: SaldoInsuficienteError):
    # Registrar el evento como warning en MongoDB
    log = LogMongo(
        evento="SaldoInsuficiente",
        mensaje=exc.mensaje,
        nivel="WARNING",
        endpoint=str(request.url),
        ip=request.client.host
    )
    await guardar_log(log)

    # Devolver respuesta estructurada al cliente
    return respuesta_error_estandar(
        detalle=exc.mensaje,
        status_code=400,
        error_type="SaldoInsuficiente"
    )


# 💳 Ejecutar una transferencia entre cuentas
def realizar_transferencia(
    usuario_id: int,
    cuenta_origen_id: int,
    datos_transaccion: TransaccionCreate,
    db: Session
) -> TransaccionOut:
    # 🔍 Buscar la cuenta origen y validar que pertenezca al usuario
    cuenta_origen = db.query(Cuenta).filter(
        Cuenta.id == cuenta_origen_id,
        Cuenta.usuario_id == usuario_id
    ).first()

    if not cuenta_origen:
        raise CuentaCongeladaError("Cuenta origen no encontrada o no pertenece al usuario.")

    # 🔍 Buscar la cuenta destino
    cuenta_destino = db.query(Cuenta).filter(
        Cuenta.id == datos_transaccion.cuenta_destino_id
    ).first()

    if not cuenta_destino:
        raise CuentaCongeladaError("Cuenta destino no encontrada.")

    # ❄️ Verificar que ambas cuentas estén activas
    if cuenta_origen.estado != EstadoCuenta.activa:
        raise CuentaCongeladaError("La cuenta origen está congelada o inactiva.")
    if cuenta_destino.estado != EstadoCuenta.activa:
        raise CuentaCongeladaError("La cuenta destino está congelada o inactiva.")

    # 💰 Verificar que el saldo sea suficiente
    if cuenta_origen.saldo < datos_transaccion.monto:
        raise SaldoInsuficienteError("El saldo de la cuenta origen no es suficiente.")

    # 🧾 Registrar la transacción en base de datos
    nueva_transaccion = Transaccion(
        cuenta_origen_id=cuenta_origen.id,
        cuenta_destino_id=cuenta_destino.id,
        monto=datos_transaccion.monto,
        tipo=datos_transaccion.tipo,
        estado="completada",
        fecha=datetime.utcnow()
    )

    # 💳 Actualizar saldos de ambas cuentas
    cuenta_origen.saldo -= datos_transaccion.monto
    cuenta_destino.saldo += datos_transaccion.monto

    # 💾 Guardar en base de datos
    db.add(nueva_transaccion)
    db.commit()
    db.refresh(nueva_transaccion)

    # 🧠 Log de éxito (opcional)
    log = LogMongo(
        evento="TransferenciaExitosa",
        mensaje=f"Se transfirieron ${datos_transaccion.monto} de cuenta {cuenta_origen.id} a {cuenta_destino.id}",
        nivel="INFO",
        usuario_id=usuario_id,
        metadata={"origen": cuenta_origen.id, "destino": cuenta_destino.id}
    )
    try:
        # Se guarda asincrónicamente pero no bloquea el proceso
        import asyncio
        asyncio.create_task(guardar_log(log))
    except:
        pass  # Silencioso por si no se puede usar asyncio

    # 📤 Devolver la transacción validada
    return TransaccionOut.model_validate(nueva_transaccion)


# 📄 Obtener historial de transacciones del usuario (como emisor o receptor)
def obtener_historial_usuario(
    usuario_id: int,
    db: Session
) -> List[TransaccionOut]:
    # 🔍 Obtener IDs de las cuentas del usuario
    cuentas_usuario = db.query(Cuenta.id).filter(Cuenta.usuario_id == usuario_id).subquery()

    # 🔁 Buscar transacciones donde el usuario es origen o destino
    transacciones = db.query(Transaccion).filter(
        or_(
            Transaccion.cuenta_origen_id.in_(cuentas_usuario),
            Transaccion.cuenta_destino_id.in_(cuentas_usuario)
        )
    ).order_by(Transaccion.fecha.desc()).all()

    # 🧾 Convertirlas a esquema Pydantic y devolver
    return [TransaccionOut.model_validate(t) for t in transacciones]