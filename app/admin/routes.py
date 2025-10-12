from fastapi import APIRouter, Depends, status, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.seguridad import get_current_user
from core.dependencias import get_db
from schemas.auth import DatosUsuarioToken
from schemas.usuario import UsuarioOut, CambiarRolUsuario
from schemas.cuenta import CambiarEstadoCuenta, CuentaOut, ActualizarSaldo
from schemas.transaccion import TransaccionOut
from schemas.logs import LogMongoOut, LogCorreoOut

from services.admin_service import (
    obtener_usuarios,
    cambiar_rol_usuario,
    cambiar_estado_cuenta,
    reporte_transacciones_por_fecha,
    resumen_cuentas_por_estado,
    reporte_usuarios_activos,
    reporte_saldos_por_tipo_cuenta,
    top_usuarios_transacciones,
)
from services.cuenta_service import actualizar_saldo_cuenta
from services.log_service import obtener_logs, obtener_logs_correos

router = APIRouter(prefix="/admin", tags=["Administración"])


# 👮 Helper para verificar que el usuario sea admin
def verificar_admin(usuario: DatosUsuarioToken) -> None:
    if usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")


# 📋 Obtener todos los usuarios (paginado desde service)
@router.get("/usuarios", response_model=List[UsuarioOut], status_code=status.HTTP_200_OK)
def listar_usuarios(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)"),
    limit: int = Query(10, le=100, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> List[UsuarioOut]:
    verificar_admin(usuario)
    return obtener_usuarios(db, skip=skip, limit=limit)

# 🔄 Cambiar rol de usuario
@router.put("/usuarios/{usuario_id}/rol", response_model=UsuarioOut)
def actualizar_rol_usuario(
    usuario_id: int,
    datos: CambiarRolUsuario,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario_actual: DatosUsuarioToken = Depends(get_current_user),
) -> UsuarioOut:
    verificar_admin(usuario_actual)

    # 🚫 Prevenir que un admin se degrade a sí mismo
    if usuario_id == usuario_actual.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")

    return cambiar_rol_usuario(
        usuario_id=usuario_id,
        datos=datos,
        db=db,
        admin_id=usuario_actual.id,
        endpoint=f"/admin/usuarios/{usuario_id}/rol",
        background_tasks=background_tasks,
    )


# 🔐 Cambiar estado de cuenta bancaria
@router.put("/cuentas/{cuenta_id}/estado", response_model=CuentaOut)
def actualizar_estado_cuenta(
    cuenta_id: int,
    datos: CambiarEstadoCuenta,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> CuentaOut:
    verificar_admin(usuario)
    return cambiar_estado_cuenta(
        cuenta_id=cuenta_id,
        datos=datos,
        db=db,
        admin_id=usuario.id,
        endpoint=f"/admin/cuentas/{cuenta_id}/estado",
        background_tasks=background_tasks,
    )


# 📊 Ver logs del sistema
@router.get("/logs", response_model=List[LogMongoOut])
async def ver_logs(
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel (INFO, WARNING, ERROR)"),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> List[LogMongoOut]:
    verificar_admin(usuario)
    return await obtener_logs(evento=evento, nivel=nivel)


# 📧 Ver logs de correos
@router.get("/logs/correos", response_model=List[LogCorreoOut])
async def ver_logs_correos(
    limit: int = Query(50, description="Cantidad máxima de registros a devolver"),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> List[LogCorreoOut]:
    verificar_admin(usuario)
    return await obtener_logs_correos(limit=limit)


# 📊 Reporte de transacciones entre fechas
@router.get("/reportes/transacciones", response_model=List[TransaccionOut])
def ver_reporte_transacciones(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> List[TransaccionOut]:
    verificar_admin(usuario)
    return reporte_transacciones_por_fecha(desde, hasta, db)


# 📊 Resumen de cuentas por estado
@router.get("/reportes/cuentas/estado", response_model=Dict[str, int])
def ver_resumen_estado_cuentas(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> Dict[str, int]:
    verificar_admin(usuario)
    return resumen_cuentas_por_estado(db)


# 📊 Reporte de usuarios activos / inactivos
@router.get("/reportes/usuarios/activos", response_model=Dict[str, int])
def ver_reporte_usuarios_activos(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> Dict[str, int]:
    verificar_admin(usuario)
    return reporte_usuarios_activos(db)


# 📊 Reporte de saldos por tipo de cuenta
@router.get("/reportes/cuentas/saldos", response_model=Dict[str, float])
def ver_reporte_saldos_por_tipo(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> Dict[str, float]:
    verificar_admin(usuario)
    return reporte_saldos_por_tipo_cuenta(db)


# 🏆 Top 10 usuarios con más transacciones
@router.get("/reportes/usuarios/top-transacciones", response_model=List[Dict[str, Any]])
def ver_top_usuarios_transacciones(
    limit: int = Query(10, le=50, description="Cantidad de usuarios a devolver"),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    verificar_admin(usuario)
    return top_usuarios_transacciones(db, limit=limit)


# 💰 Actualizar saldo de cuenta (solo admin)
@router.patch("/cuentas/{cuenta_id}/saldo", response_model=CuentaOut, status_code=status.HTTP_200_OK)
def actualizar_saldo(
    cuenta_id: int,
    datos: ActualizarSaldo,
    background_tasks: BackgroundTasks,
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permite a un **administrador** actualizar directamente el saldo de una cuenta.
    Además registra el log en segundo plano.
    """
    verificar_admin(usuario_token)

    return actualizar_saldo_cuenta(
        cuenta_id=cuenta_id,
        nuevo_saldo=datos.saldo,
        db=db,
        usuario_id=usuario_token.id,
        endpoint=f"/admin/cuentas/{cuenta_id}/saldo",
        background_tasks=background_tasks,
    )
