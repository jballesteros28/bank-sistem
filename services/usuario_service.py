from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks, Request
from models.usuario import Usuario
from schemas.usuario import UsuarioOut
from services.log_service import guardar_log
from models.log import LogMongo


# 🧾 Obtener el perfil del usuario autenticado
def obtener_usuario_actual(
    usuario_id: int,
    db: Session,
    background_tasks: BackgroundTasks,
    request: Request
) -> UsuarioOut:
    """
    Retorna los datos del usuario autenticado, registrando logs de acceso.
    
    Args:
        usuario_id (int): ID del usuario autenticado (extraído del JWT).
        db (Session): Sesión activa de la base de datos.
        background_tasks (BackgroundTasks): Tareas en segundo plano para logs.
        request (Request): Objeto de la solicitud para obtener IP y correlation_id.
    
    Returns:
        UsuarioOut: Datos del usuario en formato de salida validado.
    
    Raises:
        HTTPException: Si el usuario no existe o está desactivado.
    """

    # 🔍 Buscar el usuario
    usuario: Usuario | None = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    correlation_id = getattr(request.state, "correlation_id", None)

    # ❌ Si no existe o está inactivo
    if not usuario or not usuario.es_activo:
        log = LogMongo(
            evento="UsuarioInactivoONoEncontrado",
            mensaje=f"Intento de acceso a perfil fallido para user_id={usuario_id}",
            nivel="WARNING",
            usuario_id=usuario_id,
            endpoint=str(request.url),
            ip=request.client.host,
            correlation_id=correlation_id,
        )
        background_tasks.add_task(guardar_log, log)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no existe o está desactivado.",
        )

    # ✅ Acceso exitoso
    log = LogMongo(
        evento="UsuarioPerfilConsultado",
        mensaje=f"Usuario {usuario.email} accedió a su perfil correctamente.",
        nivel="INFO",
        usuario_id=usuario.id,
        endpoint=str(request.url),
        ip=request.client.host,
        correlation_id=correlation_id,
    )
    background_tasks.add_task(guardar_log, log)

    return UsuarioOut.model_validate(usuario)
