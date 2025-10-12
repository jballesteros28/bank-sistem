# services/admin_service.py

from fastapi import HTTPException, BackgroundTasks, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from schemas.usuario import CambiarRolUsuario, UsuarioOut
from schemas.cuenta import CambiarEstadoCuenta
from schemas.transaccion import TransaccionOut
from models.cuenta import Cuenta
from models.usuario import Usuario
from models.transaccion import Transaccion
from core.enums import EstadoCuenta
from models.log import LogMongo

# 📦 Servicios auxiliares
from services.log_service import guardar_log
from services.enviadores_email.cambio_rol import enviar_email_cambio_rol
from services.enviadores_email.cuenta_congelada import enviar_email_cuenta_congelada


# ================================================================
# 👥 Obtener todos los usuarios (paginado)
# ================================================================
def obtener_usuarios(db: Session, skip: int = 0, limit: int = 10, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> List[UsuarioOut]:
    """Devuelve todos los usuarios registrados (con paginación)."""

    usuarios: List[Usuario] = db.query(Usuario).offset(skip).limit(limit).all()

    # 🧠 Log de auditoría
    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ConsultaUsuarios",
                mensaje=f"Admin {admin_id} consultó la lista de usuarios (skip={skip}, limit={limit})",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"cantidad_devuelta": len(usuarios)},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return [UsuarioOut.model_validate(u) for u in usuarios]


# ================================================================
# 🔄 Cambiar el rol de un usuario existente
# ================================================================
def cambiar_rol_usuario(
    usuario_id: int,
    datos: CambiarRolUsuario,
    db: Session,
    admin_id: int,
    endpoint: str,
    background_tasks: BackgroundTasks,
) -> UsuarioOut:
    """Permite a un administrador cambiar el rol de un usuario."""

    usuario: Usuario | None = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    rol_anterior = usuario.rol
    usuario.rol = datos.nuevo_rol

    try:
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar rol: {str(e)}")

    if background_tasks:
        # Log principal
        try:
            nivel_log = "WARNING" if rol_anterior == "admin" and usuario.rol != "admin" else "INFO"
            log = LogMongo(
                evento="CambioRolUsuario",
                mensaje=f"Admin {admin_id} cambió el rol de {usuario.email} ({rol_anterior} → {usuario.rol})",
                nivel=nivel_log,
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={
                    "usuario_id_modificado": usuario.id,
                    "rol_anterior": rol_anterior,
                    "rol_nuevo": usuario.rol,
                },
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

        # Correo de notificación
        try:
            background_tasks.add_task(
                enviar_email_cambio_rol,
                email=usuario.email,
                nombre=usuario.nombre,
                rol_anterior=rol_anterior,
                rol_nuevo=usuario.rol,
            )
        except Exception:
            log_error = LogMongo(
                evento="ErrorNotificacionCambioRol",
                mensaje=f"No se pudo enviar mail de cambio de rol a {usuario.email}",
                nivel="ERROR",
                usuario_id=usuario.id,
                metadata={"usuario_id": usuario.id},
            )
            background_tasks.add_task(guardar_log, log_error)

    return UsuarioOut.model_validate(usuario)


# ================================================================
# ❄️ Cambiar el estado de una cuenta
# ================================================================
def cambiar_estado_cuenta(
    cuenta_id: int,
    datos: CambiarEstadoCuenta,
    db: Session,
    admin_id: int,
    endpoint: str,
    background_tasks: BackgroundTasks,
) -> Cuenta:
    """Permite a un administrador cambiar el estado de una cuenta bancaria."""

    cuenta: Cuenta | None = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    estado_anterior = cuenta.estado
    cuenta.estado = datos.nuevo_estado

    try:
        db.add(cuenta)
        db.commit()
        db.refresh(cuenta)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado de cuenta: {str(e)}")

    if background_tasks:
        # Log principal
        try:
            nivel_log = "WARNING" if cuenta.estado in [EstadoCuenta.congelada, EstadoCuenta.inactiva] else "INFO"
            log = LogMongo(
                evento="CambioEstadoCuenta",
                mensaje=f"Admin {admin_id} cambió el estado de cuenta #{cuenta.id} ({estado_anterior} → {cuenta.estado})",
                nivel=nivel_log,
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={
                    "cuenta_id": cuenta.id,
                    "usuario_afectado": cuenta.usuario_id,
                    "estado_anterior": estado_anterior,
                    "estado_nuevo": cuenta.estado,
                },
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

        # Envío de correo si aplica
        if cuenta.estado in [EstadoCuenta.congelada, EstadoCuenta.inactiva]:
            titular: Usuario | None = db.query(Usuario).filter(Usuario.id == cuenta.usuario_id).first()
            if titular:
                try:
                    background_tasks.add_task(
                        enviar_email_cuenta_congelada,
                        email=titular.email,
                        nombre=titular.nombre,
                        numero_cuenta=cuenta.numero,
                        motivo=cuenta.estado.value,
                    )
                except Exception:
                    log_error = LogMongo(
                        evento="ErrorNotificacionCuentaCongelada",
                        mensaje=f"No se pudo enviar mail de congelación a {titular.email}",
                        nivel="ERROR",
                        usuario_id=titular.id,
                        metadata={"cuenta_id": cuenta.id},
                    )
                    background_tasks.add_task(guardar_log, log_error)

    return cuenta


# ================================================================
# 📈 Reporte de transacciones entre fechas
# ================================================================
def reporte_transacciones_por_fecha(desde: datetime, hasta: datetime, db: Session, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> List[TransaccionOut]:
    transacciones = (
        db.query(Transaccion)
        .filter(and_(Transaccion.fecha >= desde, Transaccion.fecha <= hasta))
        .order_by(Transaccion.fecha.desc())
        .all()
    )

    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ReporteTransaccionesPorFecha",
                mensaje=f"Admin {admin_id} generó reporte de transacciones entre {desde} y {hasta}",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"total_resultados": len(transacciones)},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return [TransaccionOut.model_validate(t) for t in transacciones]


# ================================================================
# 📊 Resumen de cuentas por estado
# ================================================================
def resumen_cuentas_por_estado(db: Session, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> Dict[str, int]:
    resultados = db.query(Cuenta.estado, func.count()).group_by(Cuenta.estado).all()
    resumen = {estado.value: 0 for estado in EstadoCuenta}
    for estado, cantidad in resultados:
        resumen[estado] = cantidad

    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ReporteCuentasPorEstado",
                mensaje=f"Admin {admin_id} generó resumen de cuentas por estado",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"resumen": resumen},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return resumen


# ================================================================
# 📊 Reporte de usuarios activos / inactivos
# ================================================================
def reporte_usuarios_activos(db: Session, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> Dict[str, int]:
    resultados = db.query(Usuario.es_activo, func.count()).group_by(Usuario.es_activo).all()
    resumen = {"activos": 0, "inactivos": 0}
    for es_activo, cantidad in resultados:
        resumen["activos" if es_activo else "inactivos"] = cantidad

    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ReporteUsuariosActivos",
                mensaje=f"Admin {admin_id} consultó usuarios activos/inactivos",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"resumen": resumen},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return resumen


# ================================================================
# 📊 Reporte de saldos por tipo de cuenta
# ================================================================
def reporte_saldos_por_tipo_cuenta(db: Session, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> Dict[str, float]:
    resultados = db.query(Cuenta.tipo, func.sum(Cuenta.saldo)).group_by(Cuenta.tipo).all()
    resumen = {tipo.value: float(total or 0) for tipo, total in resultados}

    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ReporteSaldosPorTipo",
                mensaje=f"Admin {admin_id} generó reporte de saldos por tipo de cuenta",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"resumen": resumen},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return resumen


# ================================================================
# 🏆 Top 10 usuarios con más transacciones
# ================================================================
def top_usuarios_transacciones(db: Session, limit: int = 10, admin_id: int | None = None, endpoint: str | None = None, background_tasks: BackgroundTasks | None = None) -> List[Dict[str, Any]]:
    resultados = (
        db.query(
            Usuario.id,
            Usuario.nombre,
            Usuario.email,
            func.count(Transaccion.id).label("total_transacciones"),
        )
        .join(Cuenta, Cuenta.usuario_id == Usuario.id)
        .join(
            Transaccion,
            (Transaccion.cuenta_origen_id == Cuenta.id)
            | (Transaccion.cuenta_destino_id == Cuenta.id),
        )
        .group_by(Usuario.id, Usuario.nombre, Usuario.email)
        .order_by(func.count(Transaccion.id).desc())
        .limit(limit)
        .all()
    )

    usuarios = [
        {
            "usuario_id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "total_transacciones": u.total_transacciones,
        }
        for u in resultados
    ]

    if background_tasks and admin_id:
        try:
            log = LogMongo(
                evento="ReporteTopUsuarios",
                mensaje=f"Admin {admin_id} consultó top {limit} usuarios por transacciones",
                nivel="INFO",
                usuario_id=admin_id,
                endpoint=endpoint,
                metadata={"total_resultados": len(usuarios)},
            )
            background_tasks.add_task(guardar_log, log)
        except Exception:
            pass

    return usuarios
