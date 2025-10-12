from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request, BackgroundTasks
from models.usuario import Usuario
from core.seguridad import hash_password, verify_password, crear_token
from core.enums import RolUsuario
from schemas.auth import RegistroUsuario, LoginUsuario, TokenRespuesta
from typing import Any
from services.log_service import guardar_log
from models.log import LogMongo
from datetime import datetime, timedelta

# 👇 Enviadores especializados
from services.enviadores_email.bienvenida import enviar_email_bienvenida
from services.enviadores_email.actividad_sospechosa import enviar_email_actividad_sospechosa


# ================================================================
# 📌 Registrar usuario
# ================================================================
def registrar_usuario(
    datos: RegistroUsuario,
    db: Session,
    background_tasks: BackgroundTasks
) -> Usuario:
    """Registra un nuevo usuario y envía correo de bienvenida."""
    email = datos.email.strip().lower()
    nombre = datos.nombre.strip()
    password = datos.password.strip()

    # 📌 Verificar si ya existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        log = LogMongo(
            evento="RegistroFallido",
            mensaje=f"Intento de registro con email ya registrado: {email}",
            nivel="WARNING",
            endpoint="/auth/register"
        )
        background_tasks.add_task(guardar_log, log)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # 🔐 Crear usuario
    hashed_pw = hash_password(password)
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        hashed_password=hashed_pw,
        es_activo=True,
        rol=RolUsuario.cliente,
        intentos_fallidos=0,
        bloqueado_hasta=None
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # 📝 Log de éxito
    log = LogMongo(
        evento="RegistroExitoso",
        mensaje=f"Usuario {nuevo_usuario.email} registrado exitosamente",
        nivel="INFO",
        usuario_id=nuevo_usuario.id,
        endpoint="/auth/register"
    )
    background_tasks.add_task(guardar_log, log)

    # 📧 Enviar correo de bienvenida
    try:
        background_tasks.add_task(
            enviar_email_bienvenida,
            nombre=nuevo_usuario.nombre,
            email=nuevo_usuario.email,
        )
    except Exception as e:
        log = LogMongo(
            evento="ErrorNotificacionBienvenida",
            mensaje=f"No se pudo enviar correo de bienvenida a {nuevo_usuario.email}: {str(e)}",
            nivel="ERROR",
            usuario_id=nuevo_usuario.id,
            endpoint="/auth/register"
        )
        background_tasks.add_task(guardar_log, log)

    return nuevo_usuario


# ================================================================
# 🔐 Iniciar sesión con validaciones y lockout
# ================================================================
async def login_usuario(
    datos: LoginUsuario,
    request: Request,
    db: Session,
    background_tasks: BackgroundTasks
) -> TokenRespuesta:
    """Autenticación completa de usuario con bloqueo temporal."""
    email = datos.email.strip().lower()
    password = datos.password.strip()

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    correlation_id = getattr(request.state, "correlation_id", None)
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "desconocido")

    # 🚫 Usuario no encontrado
    if not usuario:
        log = LogMongo(
            evento="LoginFallido",
            mensaje=f"Intento de login con email inexistente: {email}",
            nivel="WARNING",
            endpoint=str(request.url),
            ip=client_ip,
            metadata={"user_agent": user_agent},
            correlation_id=correlation_id
        )
        await guardar_log(log)
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    # 🚫 Usuario inactivo
    if not usuario.es_activo:
        log = LogMongo(
            evento="LoginUsuarioInactivo",
            mensaje=f"Intento de login para usuario desactivado: {usuario.email}",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint=str(request.url),
            ip=client_ip,
            metadata={"user_agent": user_agent},
            correlation_id=correlation_id
        )
        await guardar_log(log)

        try:
            background_tasks.add_task(
                enviar_email_actividad_sospechosa,
                nombre=usuario.nombre,
                email=usuario.email,
                evento="Intento de login en cuenta desactivada",
                fecha=str(datetime.now()),
                ip=client_ip
            )
        except Exception as e:
            log = LogMongo(
                evento="ErrorNotificacionUsuarioInactivo",
                mensaje=f"Error enviando aviso a {usuario.email}: {str(e)}",
                nivel="ERROR",
                usuario_id=usuario.id,
                endpoint=str(request.url),
                correlation_id=correlation_id
            )
            background_tasks.add_task(guardar_log, log)

        raise HTTPException(status_code=403, detail="Usuario desactivado. Contacte con soporte.")

    # ⏳ Usuario bloqueado temporalmente
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > datetime.now():
        log = LogMongo(
            evento="LoginBloqueado",
            mensaje=f"Intento de login mientras usuario {usuario.email} está bloqueado",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint=str(request.url),
            ip=client_ip,
            metadata={"bloqueado_hasta": str(usuario.bloqueado_hasta)},
            correlation_id=correlation_id
        )
        await guardar_log(log)
        raise HTTPException(status_code=403, detail=f"Usuario bloqueado hasta {usuario.bloqueado_hasta}")

    # ❌ Contraseña incorrecta
    if not verify_password(password, usuario.hashed_password):
        usuario.intentos_fallidos += 1
        db.add(usuario)
        db.commit()

        log = LogMongo(
            evento="LoginFallido",
            mensaje=f"Contraseña incorrecta para email: {email}",
            nivel="WARNING",
            usuario_id=usuario.id,
            endpoint=str(request.url),
            ip=client_ip,
            metadata={
                "intentos_fallidos": usuario.intentos_fallidos,
                "user_agent": user_agent
            },
            correlation_id=correlation_id
        )
        await guardar_log(log)

        # 🚫 Bloquear después de 5 intentos
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = datetime.now() + timedelta(minutes=15)
            usuario.intentos_fallidos = 0
            db.add(usuario)
            db.commit()

            try:
                background_tasks.add_task(
                    enviar_email_actividad_sospechosa,
                    nombre=usuario.nombre,
                    email=usuario.email,
                    evento="Usuario bloqueado por múltiples intentos fallidos",
                    fecha=str(datetime.now()),
                    ip=client_ip
                )
            except Exception as e:
                log = LogMongo(
                    evento="ErrorNotificacionActividadSospechosa",
                    mensaje=f"No se pudo enviar correo a {usuario.email}: {str(e)}",
                    nivel="ERROR",
                    usuario_id=usuario.id,
                    endpoint=str(request.url),
                    correlation_id=correlation_id
                )
                background_tasks.add_task(guardar_log, log)

        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    # ✅ Login exitoso
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.add(usuario)
    db.commit()

    token_data: dict[str, Any] = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }
    access_token: str = crear_token(token_data)

    log = LogMongo(
        evento="LoginExitoso",
        mensaje=f"Login correcto para {usuario.email}",
        nivel="INFO",
        usuario_id=usuario.id,
        endpoint=str(request.url),
        ip=client_ip,
        metadata={"user_agent": user_agent},
        correlation_id=correlation_id
    )
    await guardar_log(log)

    return TokenRespuesta(access_token=access_token, token_type="bearer")
