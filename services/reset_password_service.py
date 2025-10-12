from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks, Request
from datetime import datetime, timedelta
from typing import Optional
import secrets

from models.usuario import Usuario
from models.reset_password import ResetPasswordToken
from core.seguridad import hash_password
from services.enviadores_email.reset_password import enviar_email_reset_password
from services.log_service import guardar_log
from models.log import LogMongo


# ⏱️ Configuración del reset de password
RESET_TOKEN_EXP_MINUTES: int = 15   # Token válido por 15 minutos
RESET_TOKEN_MAX_ATTEMPTS: int = 3   # Máx. intentos de validación permitidos


# 📌 1. Solicitar un reset
async def solicitar_reset(
    email: str,
    db: Session,
    background_tasks: BackgroundTasks,
    request: Optional[Request] = None
) -> None:
    """
    Genera un código de reseteo de contraseña:
    - Normaliza el email.
    - Si el usuario existe, elimina tokens previos y crea uno nuevo.
    - Envía correo con el token.
    - Registra logs (incluido intento fallido si no existe el usuario).
    """
    email_norm = email.strip().lower()
    usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email_norm).first()
    correlation_id = getattr(request.state, "correlation_id", None) if request else None

    if not usuario:
        # ⚠️ Log de intento con email inexistente
        log = LogMongo(
            evento="ResetPasswordFallido",
            mensaje=f"Solicitud de reset para email inexistente: {email_norm}",
            nivel="WARNING",
            endpoint="/auth/forgot-password",
            correlation_id=correlation_id
        )
        background_tasks.add_task(guardar_log, log)
        return  # no lanzamos error para no revelar si existe o no el usuario

    # 🧹 Eliminar tokens previos y generar uno nuevo
    db.query(ResetPasswordToken).filter(ResetPasswordToken.usuario_id == usuario.id).delete()
    token: str = secrets.token_urlsafe(8)

    reset = ResetPasswordToken(
        usuario_id=usuario.id,
        token=token,
        expiracion=datetime.now() + timedelta(minutes=RESET_TOKEN_EXP_MINUTES),
        intentos=0,
        usado=False
    )
    db.add(reset)
    db.commit()
    db.refresh(reset)

    # 📧 Notificación al usuario
    try:
        background_tasks.add_task(
            enviar_email_reset_password,
            email=usuario.email,
            nombre=usuario.nombre,
            codigo=token
        )
    except Exception as e:
        log = LogMongo(
            evento="ErrorNotificacionResetPassword",
            mensaje=f"No se pudo enviar correo de reset a {usuario.email}: {str(e)}",
            nivel="ERROR",
            usuario_id=usuario.id,
            endpoint="/auth/forgot-password",
            correlation_id=correlation_id
        )
        background_tasks.add_task(guardar_log, log)

    # 📝 Log de creación exitosa del reset
    log = LogMongo(
        evento="ResetPasswordSolicitado",
        mensaje=f"Se generó un código de reset para {usuario.email}",
        nivel="INFO",
        usuario_id=usuario.id,
        endpoint="/auth/forgot-password",
        correlation_id=correlation_id
    )
    background_tasks.add_task(guardar_log, log)


# 📌 2. Validar un reset token
async def validar_reset(
    email: str,
    token: str,
    db: Session,
    background_tasks: Optional[BackgroundTasks] = None,
    request: Optional[Request] = None
) -> ResetPasswordToken:
    """
    Valida un token de reseteo:
    - Verifica existencia de usuario y token.
    - Chequea expiración, uso previo e intentos.
    - Registra logs de cada caso.
    """
    email_norm = email.strip().lower()
    usuario: Optional[Usuario] = db.query(Usuario).filter(Usuario.email == email_norm).first()
    correlation_id = getattr(request.state, "correlation_id", None) if request else None

    if not usuario:
        log = LogMongo(
            evento="ResetPasswordUsuarioNoEncontrado",
            mensaje=f"Intento de validar reset para email inexistente: {email_norm}",
            nivel="WARNING",
            endpoint="/auth/validate-reset",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    reset: Optional[ResetPasswordToken] = (
        db.query(ResetPasswordToken)
        .filter(ResetPasswordToken.usuario_id == usuario.id, ResetPasswordToken.token == token)
        .first()
    )

    if not reset:
        log = LogMongo(
            evento="ResetPasswordCodigoInvalido",
            mensaje=f"Código inválido para {email_norm}",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint="/auth/validate-reset",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="Código inválido")

    # 🚫 Token ya usado
    if reset.usado:
        log = LogMongo(
            evento="ResetPasswordCodigoUsado",
            mensaje=f"Código ya usado para {email_norm}",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint="/auth/validate-reset",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="Código ya utilizado")

    # 🚫 Máx. intentos superados
    if reset.intentos >= RESET_TOKEN_MAX_ATTEMPTS:
        log = LogMongo(
            evento="ResetPasswordCodigoBloqueado",
            mensaje=f"Código bloqueado por intentos para {email_norm}",
            nivel="ERROR",
            usuario_id=usuario.id,
            endpoint="/auth/validate-reset",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="Código bloqueado por intentos fallidos")

    # 🚫 Token expirado
    if reset.expiracion < datetime.now():
        log = LogMongo(
            evento="ResetPasswordCodigoExpirado",
            mensaje=f"Código expirado para {email_norm}",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint="/auth/validate-reset",
            correlation_id=correlation_id
        )
        if background_tasks:
            background_tasks.add_task(guardar_log, log)
        raise HTTPException(status_code=400, detail="Código expirado")

    # ✅ Validación correcta
    log = LogMongo(
        evento="ResetPasswordCodigoValido",
        mensaje=f"Código válido para {email_norm}",
        nivel="INFO",
        usuario_id=usuario.id,
        endpoint="/auth/validate-reset",
        correlation_id=correlation_id
    )
    if background_tasks:
        background_tasks.add_task(guardar_log, log)

    return reset


# 📌 3. Confirmar reset y cambiar contraseña
async def confirmar_reset(
    email: str,
    token: str,
    nueva_password: str,
    db: Session,
    background_tasks: BackgroundTasks,
    request: Optional[Request] = None
) -> None:
    """
    Confirma un reseteo de contraseña:
    - Valida token.
    - Cambia la contraseña del usuario.
    - Marca el token como usado.
    - Registra log de éxito.
    """
    reset = await validar_reset(email, token, db, background_tasks, request)
    usuario: Usuario | None = db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    usuario.hashed_password = hash_password(nueva_password.strip())
    reset.usado = True
    db.add_all([usuario, reset])
    db.commit()

    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    log = LogMongo(
        evento="ResetPasswordExitoso",
        mensaje=f"Usuario {usuario.email} cambió su contraseña correctamente",
        nivel="INFO",
        usuario_id=usuario.id,
        endpoint="/auth/reset-password",
        correlation_id=correlation_id
    )
    background_tasks.add_task(guardar_log, log)


# 📌 4. Registrar intento fallido de validación
async def registrar_intento_fallido(
    reset: ResetPasswordToken,
    db: Session
) -> None:
    """Incrementa el contador de intentos fallidos para un token de reset."""
    reset.intentos += 1
    db.add(reset)
    db.commit()
    db.refresh(reset)
