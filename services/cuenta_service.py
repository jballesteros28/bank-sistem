from sqlalchemy.orm import Session
from models.cuenta import Cuenta
from models.usuario import Usuario
from services.log_service import guardar_log
from services.enviadores_email.cuenta_creada import enviar_email_cuenta_creada
from services.enviadores_email.ajuste_saldo import enviar_email_ajuste_saldo
from models.log import LogMongo
from schemas.cuenta import CuentaCreate, CuentaOut
from fastapi import HTTPException, status, BackgroundTasks, Request
from core.enums import EstadoCuenta
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP
import random


# ==========================================================
# 🧾 Generar número de cuenta único
# ==========================================================
def generar_numero_cuenta(db: Session) -> str:
    """Genera un número de cuenta único en formato CTA-XXXXXX."""
    while True:
        numero = f"CTA-{random.randint(100000, 999999)}"
        if not db.query(Cuenta).filter(Cuenta.numero == numero).first():
            return numero


# ==========================================================
# 🏦 Crear cuenta para un usuario
# ==========================================================
def crear_cuenta(
    cuenta_datos: CuentaCreate,
    usuario_id: int,
    db: Session,
    background_tasks: BackgroundTasks,
    request: Optional[Request] = None
) -> CuentaOut:
    """Crea una nueva cuenta bancaria y envía correo de confirmación."""
    cuenta_existente = db.query(Cuenta).filter(
        Cuenta.usuario_id == usuario_id,
        Cuenta.tipo == cuenta_datos.tipo,
        Cuenta.estado != EstadoCuenta.inactiva,
    ).first()

    if cuenta_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya tienes una cuenta de tipo '{cuenta_datos.tipo.value}'."
        )

    nueva_cuenta = Cuenta(
        numero=generar_numero_cuenta(db),
        tipo=cuenta_datos.tipo,
        saldo=Decimal("0.00"),
        estado=EstadoCuenta.activa,
        usuario_id=usuario_id,
    )
    db.add(nueva_cuenta)
    db.commit()
    db.refresh(nueva_cuenta)

    titular = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if background_tasks:
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        try:
            log = LogMongo(
                evento="CuentaCreada",
                mensaje=f"Se creó la cuenta {nueva_cuenta.numero} para el usuario {usuario_id}",
                nivel="INFO",
                usuario_id=usuario_id,
                endpoint="/cuentas/",
                metadata={
                    "cuenta_id": nueva_cuenta.id,
                    "numero_cuenta": nueva_cuenta.numero,
                    "tipo_cuenta": nueva_cuenta.tipo.value,
                    "estado": nueva_cuenta.estado.value,
                },
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

        # 📧 Enviar correo de confirmación
        if titular:
            try:
                background_tasks.add_task(
                    enviar_email_cuenta_creada,
                    email=titular.email,
                    nombre=titular.nombre,
                    numero_cuenta=nueva_cuenta.numero,
                    tipo_cuenta=nueva_cuenta.tipo.value,
                    saldo_inicial=nueva_cuenta.saldo,
                    estado=nueva_cuenta.estado.value,
                )
            except Exception as e:
                log = LogMongo(
                    evento="ErrorNotificacionCuentaCreada",
                    mensaje=f"No se pudo enviar mail de creación de cuenta a {titular.email}: {str(e)}",
                    nivel="ERROR",
                    usuario_id=usuario_id,
                    metadata={"cuenta_id": nueva_cuenta.id},
                    correlation_id=correlation_id
                )
                background_tasks.add_task(guardar_log, log)

    return CuentaOut.model_validate(nueva_cuenta)


# ==========================================================
# 📂 Listar todas las cuentas de un usuario
# ==========================================================
def obtener_cuentas_usuario(
    usuario_id: int,
    db: Session,
    background_tasks: Optional[BackgroundTasks] = None,
    request: Optional[Request] = None
) -> List[CuentaOut]:
    """Devuelve todas las cuentas de un usuario."""
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == usuario_id).all()

    if not cuentas:
        # 🔸 Log de advertencia si no tiene cuentas
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        log = LogMongo(
            evento="CuentasNoEncontradas",
            mensaje=f"Usuario {usuario_id} no tiene cuentas registradas.",
            nivel="WARNING",
            usuario_id=usuario_id,
            endpoint="/cuentas/",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene cuentas registradas."
        )

    return [CuentaOut.model_validate(cuenta) for cuenta in cuentas]


# ==========================================================
# 📌 Obtener una cuenta específica
# ==========================================================
def obtener_cuenta_por_id(
    cuenta_id: int,
    usuario_id: int,
    db: Session,
    background_tasks: Optional[BackgroundTasks] = None,
    request: Optional[Request] = None
) -> CuentaOut:
    """Devuelve una cuenta específica perteneciente a un usuario."""
    cuenta = db.query(Cuenta).filter(
        Cuenta.id == cuenta_id,
        Cuenta.usuario_id == usuario_id,
    ).first()

    if not cuenta:
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        log = LogMongo(
            evento="CuentaNoEncontrada",
            mensaje=f"Intento de acceso a cuenta inexistente o ajena (user={usuario_id}, cuenta={cuenta_id})",
            nivel="WARNING",
            usuario_id=usuario_id,
            endpoint="/cuentas/{id}",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada o no pertenece al usuario."
        )

    return CuentaOut.model_validate(cuenta)


# ==========================================================
# 💰 Actualizar saldo (solo admins)
# ==========================================================
def actualizar_saldo_cuenta(
    cuenta_id: int,
    nuevo_saldo: Decimal,
    db: Session,
    usuario_id: Optional[int] = None,
    endpoint: str = "/admin/cuentas/{id}/saldo",
    background_tasks: Optional[BackgroundTasks] = None,
    request: Optional[Request] = None
) -> CuentaOut:
    """Actualiza el saldo de una cuenta (uso administrativo)."""
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()

    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")

    if nuevo_saldo < 0:
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        log = LogMongo(
            evento="IntentoSaldoNegativo",
            mensaje=f"Intento de asignar saldo negativo a cuenta #{cuenta_id} por usuario {usuario_id}",
            nivel="WARNING",
            usuario_id=usuario_id,
            endpoint=endpoint,
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="El saldo no puede ser negativo.")

    saldo_anterior = Decimal(cuenta.saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    nuevo_saldo_normalizado = Decimal(nuevo_saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cuenta.saldo = nuevo_saldo_normalizado

    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)

    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    if background_tasks:
        # 🧾 Log administrativo
        try:
            log = LogMongo(
                evento="ActualizarSaldoCuenta",
                mensaje=f"Admin {usuario_id} actualizó saldo de cuenta #{cuenta.id}: {saldo_anterior} → {nuevo_saldo_normalizado}",
                nivel="INFO",
                usuario_id=usuario_id,
                endpoint=endpoint,
                metadata={
                    "cuenta_id": cuenta.id,
                    "saldo_anterior": str(saldo_anterior),
                    "nuevo_saldo": str(nuevo_saldo_normalizado),
                },
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

        # 📧 Notificar titular
        titular = db.query(Usuario).filter(Usuario.id == cuenta.usuario_id).first()
        if titular:
            try:
                background_tasks.add_task(
                    enviar_email_ajuste_saldo,
                    email=titular.email,
                    nombre=titular.nombre,
                    numero_cuenta=cuenta.numero,
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=cuenta.saldo,
                )
            except Exception as e:
                log = LogMongo(
                    evento="ErrorNotificacionAjusteSaldo",
                    mensaje=f"No se pudo enviar mail de ajuste de saldo a {titular.email}: {str(e)}",
                    nivel="ERROR",
                    usuario_id=titular.id,
                    metadata={"cuenta_id": cuenta.id},
                    correlation_id=correlation_id
                )
                background_tasks.add_task(guardar_log, log)

    return CuentaOut.model_validate(cuenta)
