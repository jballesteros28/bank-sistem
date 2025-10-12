# services/log_summary_service.py
# -*- coding: utf-8 -*-

"""
📊 Servicio de resumen de logs del sistema
-----------------------------------------
Este módulo genera reportes agregados a partir de los logs persistidos en MongoDB.
Se utiliza para alimentar el dashboard administrativo (/admin/logs/...).

Incluye:
- Resumen de transacciones (por evento y por día)
- Resumen de correos (por estado y por plantilla)
- Resumen de niveles de log (INFO, WARNING, ERROR)
- Resumen general consolidado
- NUEVO: resumen_dashboard() → datos formateados para el dashboard React
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore

# ✅ Conexión global a Mongo desde tu módulo de base de datos
from database.db_mongo import mongo_db

# 📂 Nombres de colecciones
COL_LOGS = "logs"
COL_LOGS_CORREO = "logs_correos"


# ─────────────────────────────────────────────────────────────
# 📘 Tipos de ayuda (para autocompletado y validación)
# ─────────────────────────────────────────────────────────────
class ConteoPorClave(TypedDict):
    _id: str
    total: int

class ConteoTemporal(TypedDict):
    _id: str
    total: int

class ResumenTransacciones(TypedDict, total=False):
    por_evento: List[ConteoPorClave]
    por_dia: List[ConteoTemporal]

class ResumenCorreos(TypedDict, total=False):
    por_estado: List[ConteoPorClave]
    top_templates: List[ConteoPorClave]

class ResumenNiveles(TypedDict):
    por_nivel: List[ConteoPorClave]

class ResumenGeneral(TypedDict, total=False):
    transacciones: ResumenTransacciones
    correos: ResumenCorreos
    niveles: ResumenNiveles


# ─────────────────────────────────────────────────────────────
# 🔧 Utilidades para construir filtros y pipelines de Mongo
# ─────────────────────────────────────────────────────────────
def _filtro_fecha(desde: Optional[datetime], hasta: Optional[datetime]) -> Dict[str, Any]:
    """Construye un filtro por rango de fechas sobre el campo 'fecha'."""
    if not desde and not hasta:
        return {}
    rango: Dict[str, Any] = {}
    if desde:
        rango["$gte"] = desde
    if hasta:
        rango["$lte"] = hasta
    return {"fecha": rango}


def _match_base(
    *,
    eventos: Optional[List[str]] = None,
    usuario_id: Optional[int] = None,
    nivel: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Crea un filtro base para el $match en las agregaciones."""
    match: Dict[str, Any] = {}
    if eventos:
        match["evento"] = {"$in": eventos}
    if usuario_id is not None:
        match["usuario_id"] = usuario_id
    if nivel:
        match["nivel"] = nivel
    match.update(_filtro_fecha(desde, hasta))
    return match


def _pipeline_conteo_por_clave(match: Dict[str, Any], clave: str = "$evento", ordenar_desc: bool = True) -> List[Dict[str, Any]]:
    """Pipeline genérico: agrupa por 'clave' (campo) y cuenta ocurrencias."""
    pipeline: List[Dict[str, Any]] = [
        {"$match": match},
        {"$group": {"_id": clave, "total": {"$sum": 1}}},
    ]
    if ordenar_desc:
        pipeline.append({"$sort": {"total": -1}})
    return pipeline


def _pipeline_conteo_por_dia(match: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pipeline para agrupar por día (YYYY-MM-DD) según el campo 'fecha'."""
    return [
        {"$match": match},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha"}},
                "total": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]


# ─────────────────────────────────────────────────────────────
# 📊 Servicios de resumen de logs
# ─────────────────────────────────────────────────────────────
async def resumen_transacciones(*, db: AsyncIOMotorDatabase[Any] = mongo_db,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None, usuario_id: Optional[int] = None) -> ResumenTransacciones:

    eventos_interes = ["TransferenciaExitosa", "TransferenciaFallida", "TransferenciaSaldoInsuficiente"]
    match = _match_base(eventos=eventos_interes, usuario_id=usuario_id, desde=desde, hasta=hasta)

    por_evento = await db[COL_LOGS].aggregate(_pipeline_conteo_por_clave(match, clave="$evento")).to_list(length=None)
    por_dia = await db[COL_LOGS].aggregate(_pipeline_conteo_por_dia(match)).to_list(length=None)
    return {"por_evento": por_evento, "por_dia": por_dia}


async def resumen_correos(*, db: AsyncIOMotorDatabase[Any] = mongo_db,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None, top_n_templates: int = 5) -> ResumenCorreos:

    match = _filtro_fecha(desde, hasta)
    pipeline_estado = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    por_estado = await db[COL_LOGS_CORREO].aggregate(pipeline_estado).to_list(length=None)

    pipeline_templates = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {"_id": "$template", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": top_n_templates},
    ]
    top_templates = await db[COL_LOGS_CORREO].aggregate(pipeline_templates).to_list(length=None)
    return {"por_estado": por_estado, "top_templates": top_templates}


async def resumen_niveles(*, db: AsyncIOMotorDatabase[Any] = mongo_db,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None, usuario_id: Optional[int] = None) -> ResumenNiveles:

    match = _match_base(desde=desde, hasta=hasta, usuario_id=usuario_id)
    por_nivel = await db[COL_LOGS].aggregate(_pipeline_conteo_por_clave(match, clave="$nivel")).to_list(length=None)
    return {"por_nivel": por_nivel}


async def resumen_general(*, db: AsyncIOMotorDatabase[Any] = mongo_db,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None,
    usuario_id: Optional[int] = None, incluir_correos: bool = True, incluir_niveles: bool = True) -> ResumenGeneral:

    resultado: ResumenGeneral = {}
    resultado["transacciones"] = await resumen_transacciones(db=db, desde=desde, hasta=hasta, usuario_id=usuario_id)
    if incluir_correos:
        resultado["correos"] = await resumen_correos(db=db, desde=desde, hasta=hasta)
    if incluir_niveles:
        resultado["niveles"] = await resumen_niveles(db=db, desde=desde, hasta=hasta, usuario_id=usuario_id)
    return resultado


# ─────────────────────────────────────────────────────────────
# 📈 NUEVO — Formato especial para dashboard React
# ─────────────────────────────────────────────────────────────
async def resumen_dashboard(
    *, db: AsyncIOMotorDatabase[Any] = mongo_db,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Devuelve los datos listos para graficar en el dashboard React:
    - niveles_chart → barras por nivel (INFO, WARNING, ERROR)
    - correos_chart → torta de estados y top templates
    - transacciones_chart → línea temporal diaria
    """
    data = await resumen_general(db=db, desde=desde, hasta=hasta)

    def formatear_para_chart(lista: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        return {
            "labels": [item["_id"] for item in lista],
            "values": [item["total"] for item in lista],
        }

    return {
        "niveles_chart": formatear_para_chart(data["niveles"]["por_nivel"]),
        "correos_chart": formatear_para_chart(data["correos"]["top_templates"]),
        "transacciones_chart": formatear_para_chart(data["transacciones"]["por_dia"]),
    }
