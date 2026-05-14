from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.enums import RolUsuario
from core.seguridad import get_current_user, is_admin_or_super_admin, is_super_admin
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from models.usuario import Usuario
from schemas.auth import DatosUsuarioToken
from schemas.cuenta import ActualizarSaldo, CambiarEstadoCuenta, CuentaOut
from schemas.logs import LogCorreoOut, LogMongoOut
from schemas.transaccion import TransaccionOut
from schemas.usuario import CambiarRolUsuario, UsuarioOut
from services.admin_service import (
    cambiar_estado_cuenta,
    cambiar_rol_usuario,
    obtener_usuarios,
    reporte_saldos_por_tipo_cuenta,
    reporte_transacciones_por_fecha,
    reporte_usuarios_activos,
    resumen_cuentas_por_estado,
    top_usuarios_transacciones,
)
from services.cuenta_service import actualizar_saldo_cuenta
from services.log_service import obtener_logs, obtener_logs_correos


router = APIRouter(prefix="/admin", tags=["Administración"])


def verificar_admin(usuario: DatosUsuarioToken) -> None:
    """Permite admins de tenant y super admins globales."""
    if not is_admin_or_super_admin(usuario):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")


def _scope_organizacion(
    usuario: DatosUsuarioToken,
    organizacion: Organizacion,
) -> UUID | None:
    """Super admin opera globalmente; admin comun queda limitado a su organizacion."""
    return None if is_super_admin(usuario) else organizacion.id


def _usuarios_en_scope(db: Session, organizacion_id: UUID | None) -> list[int] | None:
    """Devuelve ids de usuarios visibles para filtrar logs generales."""
    if organizacion_id is None:
        return None
    return [
        usuario_id
        for (usuario_id,) in db.query(Usuario.id)
        .filter(Usuario.organizacion_id == organizacion_id)
        .all()
    ]


@router.get("/usuarios", response_model=list[UsuarioOut], status_code=status.HTTP_200_OK)
def listar_usuarios(
    skip: int = Query(0, ge=0, description="Numero de registros a saltar"),
    limit: int = Query(10, le=100, description="Numero maximo de registros a devolver"),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[UsuarioOut]:
    verificar_admin(usuario)
    return obtener_usuarios(
        db,
        skip=skip,
        limit=limit,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.put("/usuarios/{usuario_id}/rol", response_model=UsuarioOut)
def actualizar_rol_usuario(
    usuario_id: int,
    datos: CambiarRolUsuario,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario_actual: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> UsuarioOut:
    verificar_admin(usuario_actual)

    if usuario_id == usuario_actual.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")
    if not is_super_admin(usuario_actual) and datos.nuevo_rol == RolUsuario.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Solo super_admin puede asignar ese rol.")

    return cambiar_rol_usuario(
        usuario_id=usuario_id,
        datos=datos,
        db=db,
        admin_id=usuario_actual.id,
        endpoint=f"/admin/usuarios/{usuario_id}/rol",
        background_tasks=background_tasks,
        organizacion_id=_scope_organizacion(usuario_actual, organizacion),
    )


@router.put("/cuentas/{cuenta_id}/estado", response_model=CuentaOut)
def actualizar_estado_cuenta(
    cuenta_id: int,
    datos: CambiarEstadoCuenta,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> CuentaOut:
    verificar_admin(usuario)
    return cambiar_estado_cuenta(
        cuenta_id=cuenta_id,
        datos=datos,
        db=db,
        admin_id=usuario.id,
        endpoint=f"/admin/cuentas/{cuenta_id}/estado",
        background_tasks=background_tasks,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.get("/logs", response_model=list[LogMongoOut])
async def ver_logs(
    evento: str | None = Query(None, description="Filtrar por tipo de evento"),
    nivel: str | None = Query(None, description="Filtrar por nivel"),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[LogMongoOut]:
    verificar_admin(usuario)
    scope = _scope_organizacion(usuario, organizacion)
    return await obtener_logs(
        evento=evento,
        nivel=nivel,
        usuario_ids=_usuarios_en_scope(db, scope),
    )


@router.get("/logs/correos", response_model=list[LogCorreoOut])
async def ver_logs_correos(
    limit: int = Query(50, description="Cantidad maxima de registros a devolver"),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[LogCorreoOut]:
    verificar_admin(usuario)
    if not is_super_admin(usuario):
        # Los logs de correos no guardan tenant; evitamos exponer datos cruzados.
        return []
    return await obtener_logs_correos(limit=limit)


@router.get("/reportes/transacciones", response_model=list[TransaccionOut])
def ver_reporte_transacciones(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[TransaccionOut]:
    verificar_admin(usuario)
    return reporte_transacciones_por_fecha(
        desde,
        hasta,
        db,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.get("/reportes/cuentas/estado", response_model=dict[str, int])
def ver_resumen_estado_cuentas(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> dict[str, int]:
    verificar_admin(usuario)
    return resumen_cuentas_por_estado(
        db,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.get("/reportes/usuarios/activos", response_model=dict[str, int])
def ver_reporte_usuarios_activos(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> dict[str, int]:
    verificar_admin(usuario)
    return reporte_usuarios_activos(
        db,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.get("/reportes/cuentas/saldos", response_model=dict[str, float])
def ver_reporte_saldos_por_tipo(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> dict[str, float]:
    verificar_admin(usuario)
    return reporte_saldos_por_tipo_cuenta(
        db,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.get("/reportes/usuarios/top-transacciones", response_model=list[dict[str, Any]])
def ver_top_usuarios_transacciones(
    limit: int = Query(10, le=50, description="Cantidad de usuarios a devolver"),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[dict[str, Any]]:
    verificar_admin(usuario)
    return top_usuarios_transacciones(
        db,
        limit=limit,
        organizacion_id=_scope_organizacion(usuario, organizacion),
    )


@router.patch("/cuentas/{cuenta_id}/saldo", response_model=CuentaOut, status_code=status.HTTP_200_OK)
def actualizar_saldo(
    cuenta_id: int,
    datos: ActualizarSaldo,
    background_tasks: BackgroundTasks,
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> CuentaOut:
    verificar_admin(usuario_token)
    return actualizar_saldo_cuenta(
        cuenta_id=cuenta_id,
        nuevo_saldo=datos.saldo,
        db=db,
        usuario_id=usuario_token.id,
        organizacion_id=_scope_organizacion(usuario_token, organizacion),
        endpoint=f"/admin/cuentas/{cuenta_id}/saldo",
        background_tasks=background_tasks,
    )
