from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from core.seguridad import get_current_user
from core.dependencias import get_db
from schemas.auth import DatosUsuarioToken
from schemas.usuario import UsuarioOut, CambiarRolUsuario
from schemas.cuenta import CambiarEstadoCuenta, CuentaOut
from schemas.transaccion import TransaccionOut
from services.admin_service import (obtener_usuarios,
                                    cambiar_rol_usuario,
                                    cambiar_estado_cuenta,
                                    reporte_transacciones_por_fecha,
                                    resumen_cuentas_por_estado
                                    )
from services.log_service import obtener_logs
from typing import Optional
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=["Administración"]
)

# 👮 Verificación de rol admin
def verificar_admin(usuario: DatosUsuarioToken):
    if usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")

# 📋 Ruta para obtener todos los usuarios (solo admin)
@router.get("/usuarios", response_model=list[UsuarioOut], status_code=status.HTTP_200_OK)
def listar_usuarios(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Devuelve la lista de todos los usuarios del sistema. Solo accesible por administradores.
    """
    verificar_admin(usuario)
    return obtener_usuarios(db)


# 🔄 Ruta: cambiar el rol de un usuario (solo admin)
@router.put("/usuarios/{usuario_id}/rol", response_model=UsuarioOut)
def actualizar_rol_usuario(
    usuario_id: int,
    datos: CambiarRolUsuario,
    db: Session = Depends(get_db),
    usuario_actual: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Permite a un administrador cambiar el rol de otro usuario.
    """
    verificar_admin(usuario_actual)
    return cambiar_rol_usuario(usuario_id, datos, db)



# 🔐 Ruta: cambiar estado de una cuenta bancaria
@router.put("/cuentas/{cuenta_id}/estado", response_model=CuentaOut)
def actualizar_estado_cuenta(
    cuenta_id: int,
    datos: CambiarEstadoCuenta,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Permite al administrador cambiar el estado de una cuenta (activa, congelada, inactiva).
    """
    verificar_admin(usuario)
    return cambiar_estado_cuenta(cuenta_id, datos, db)


# 📊 Ruta: obtener los últimos logs del sistema (admin only)
@router.get("/logs")
async def ver_logs(
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel (INFO, WARNING, ERROR)"),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Devuelve los últimos logs del sistema. Solo para administradores.
    """
    verificar_admin(usuario)
    return await obtener_logs(evento=evento, nivel=nivel)



# 📊 Ruta: reporte de transacciones entre fechas (solo admin)
@router.get("/reportes/transacciones", response_model=list[TransaccionOut])
def ver_reporte_transacciones(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Devuelve todas las transacciones entre dos fechas específicas.
    """
    verificar_admin(usuario)
    return reporte_transacciones_por_fecha(desde, hasta, db)



# 📊 Ruta: resumen de cuentas por estado
@router.get("/reportes/cuentas/estado", response_model=dict)
def ver_resumen_estado_cuentas(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Devuelve la cantidad de cuentas agrupadas por estado (activa, inactiva, congelada).
    """
    verificar_admin(usuario)
    return resumen_cuentas_por_estado(db)