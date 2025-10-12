# routes/admin/logs_routes.py
# -*- coding: utf-8 -*-

"""
📊 Rutas administrativas para visualizar y resumir logs del sistema.
Incluye endpoints de resumen por tipo de evento, correos, niveles, resumen y dashboard.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Servicios de resumen
# ─────────────────────────────────────────────────────────────
from services.log_summary_service import (
    resumen_transacciones,
    resumen_correos,
    resumen_niveles,
    resumen_general,
    resumen_dashboard,  # ✅ NUEVO
)

# ─────────────────────────────────────────────────────────────
# Seguridad y dependencias
# ─────────────────────────────────────────────────────────────
from core.seguridad import get_current_admin
from schemas.auth import DatosUsuarioToken

router = APIRouter(prefix="/admin/logs", tags=["📊 Logs Administrativos"])


# 🧾 Utilidad para convertir string a datetime
def parse_datetime_or_none(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de fecha inválido: {valor}. Usa ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM).",
        )


# 📈 Resumen de transacciones
@router.get("/transacciones")
async def obtener_resumen_transacciones(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    admin: DatosUsuarioToken = Depends(get_current_admin),
):
    return await resumen_transacciones(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
    )


# ✉️ Resumen de correos
@router.get("/correos")
async def obtener_resumen_correos(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    top_n: int = Query(5),
    admin: DatosUsuarioToken = Depends(get_current_admin),
):
    return await resumen_correos(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        top_n_templates=top_n,
    )


# ⚠️ Resumen por niveles
@router.get("/niveles")
async def obtener_resumen_niveles(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    admin: DatosUsuarioToken = Depends(get_current_admin),
):
    return await resumen_niveles(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
    )


# 🧮 Resumen general consolidado
@router.get("/resumen")
async def obtener_resumen_general(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    incluir_correos: bool = Query(True),
    incluir_niveles: bool = Query(True),
    admin: DatosUsuarioToken = Depends(get_current_admin),
):
    return await resumen_general(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
        usuario_id=usuario_id,
        incluir_correos=incluir_correos,
        incluir_niveles=incluir_niveles,
    )


# 🌐 NUEVO — Datos optimizados para dashboard React
@router.get("/dashboard", summary="Datos listos para dashboard React")
async def obtener_dashboard_logs(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    admin: DatosUsuarioToken = Depends(get_current_admin),
):
    """
    Devuelve un JSON con tres estructuras listas para graficar:
    - niveles_chart
    - correos_chart
    - transacciones_chart
    """
    return await resumen_dashboard(
        desde=parse_datetime_or_none(desde),
        hasta=parse_datetime_or_none(hasta),
    )
