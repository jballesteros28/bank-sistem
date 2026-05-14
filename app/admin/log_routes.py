from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_user, is_admin_or_super_admin, is_super_admin
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from models.usuario import Usuario
from schemas.auth import DatosUsuarioToken
from services.log_summary_service import (
    resumen_correos,
    resumen_dashboard,
    resumen_general,
    resumen_niveles,
    resumen_transacciones,
)


router = APIRouter(prefix="/admin/logs", tags=["Auditoría / Logs"])


def parse_datetime_or_none(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de fecha invalido: {valor}. Usa ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM).",
        )


def _verificar_admin(usuario: DatosUsuarioToken) -> None:
    """Permite admins de tenant y super admins."""
    if not is_admin_or_super_admin(usuario):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")


def _scope_organizacion(usuario: DatosUsuarioToken, organizacion: Organizacion) -> UUID | None:
    """Super admin consulta global; admin comun queda limitado a su organizacion."""
    return None if is_super_admin(usuario) else organizacion.id


def _usuarios_en_scope(db: Session, organizacion_id: UUID | None) -> list[int] | None:
    if organizacion_id is None:
        return None
    return [
        usuario_id
        for (usuario_id,) in db.query(Usuario.id)
        .filter(Usuario.organizacion_id == organizacion_id)
        .all()
    ]


def _validar_usuario_log(usuario_id: int | None, usuario_ids: list[int] | None) -> None:
    """Evita que un admin filtre logs de usuarios de otro tenant."""
    if usuario_id is not None and usuario_ids is not None and usuario_id not in usuario_ids:
        raise HTTPException(status_code=403, detail="Usuario fuera de la organizacion.")


@router.get("/transacciones")
async def obtener_resumen_transacciones(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    usuario_id: int | None = Query(None),
    db: Session = Depends(get_db),
    admin: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
):
    _verificar_admin(admin)
    usuario_ids = _usuarios_en_scope(db, _scope_organizacion(admin, organizacion))
    _validar_usuario_log(usuario_id, usuario_ids)
    return await resumen_transacciones(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
        usuario_ids=usuario_ids if usuario_id is None else None,
    )


@router.get("/correos")
async def obtener_resumen_correos(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    top_n: int = Query(5),
    admin: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
):
    _verificar_admin(admin)
    if not is_super_admin(admin):
        # Los logs de correos no tienen tenant persistido; no se exponen entre organizaciones.
        return {"por_estado": [], "top_templates": []}
    return await resumen_correos(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        top_n_templates=top_n,
    )


@router.get("/niveles")
async def obtener_resumen_niveles(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    usuario_id: int | None = Query(None),
    db: Session = Depends(get_db),
    admin: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
):
    _verificar_admin(admin)
    usuario_ids = _usuarios_en_scope(db, _scope_organizacion(admin, organizacion))
    _validar_usuario_log(usuario_id, usuario_ids)
    return await resumen_niveles(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
        usuario_ids=usuario_ids if usuario_id is None else None,
    )


@router.get("/resumen")
async def obtener_resumen_general(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    usuario_id: int | None = Query(None),
    incluir_correos: bool = Query(True),
    incluir_niveles: bool = Query(True),
    db: Session = Depends(get_db),
    admin: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
):
    _verificar_admin(admin)
    scope = _scope_organizacion(admin, organizacion)
    usuario_ids = _usuarios_en_scope(db, scope)
    _validar_usuario_log(usuario_id, usuario_ids)
    return await resumen_general(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
        usuario_ids=usuario_ids if usuario_id is None else None,
        incluir_correos=incluir_correos and scope is None,
        incluir_niveles=incluir_niveles,
    )


@router.get("/dashboard", summary="Datos listos para dashboard React")
async def obtener_dashboard_logs(
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    db: Session = Depends(get_db),
    admin: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
):
    _verificar_admin(admin)
    scope = _scope_organizacion(admin, organizacion)
    return await resumen_dashboard(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_ids=_usuarios_en_scope(db, scope),
        incluir_correos=scope is None,
    )
