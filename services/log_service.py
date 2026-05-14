# services/log_service.py
from models.log import LogMongo, LogCorreo
from database.db_mongo import mongo_db, get_logs_collection
from pymongo.errors import PyMongoError
from typing import List, Optional, Any
import contextvars

# 🧩 ContextVar para almacenar correlation_id en cada request automáticamente
correlation_id_ctx = contextvars.ContextVar("correlation_id", default=None)


# 📝 Guardar log en la colección de MongoDB
async def guardar_log(log: LogMongo) -> Optional[str]:
    try:
        # 👇 Si el log no tiene correlation_id, lo insertamos desde el contexto
        correlation_id = correlation_id_ctx.get()
        if correlation_id and "correlation_id" not in log.dict():
            log.correlation_id = correlation_id

        result = await mongo_db.logs.insert_one(log.dict())
        return str(result.inserted_id)
    except PyMongoError as e:
        print(f"[Logger MongoDB] No se pudo guardar el log: {e}")
        return None


# 📄 Obtener logs desde MongoDB con filtros opcionales
async def obtener_logs(
    evento: Optional[str] = None,
    nivel: Optional[str] = None,
    correlation_id: Optional[str] = None,
    usuario_ids: Optional[list[int]] = None,
) -> List[dict[Any, Any]]:
    coleccion = get_logs_collection()

    query = {}
    if evento:
        query["evento"] = evento
    if nivel:
        query["nivel"] = nivel
    if usuario_ids is not None:
        # Admins comunes solo ven logs de usuarios de su organizacion.
        query["usuario_id"] = {"$in": usuario_ids}
    if correlation_id:
        query["correlation_id"] = correlation_id
    else:
        # Si no se pasa, usamos el del contexto
        ctx_correlation_id = correlation_id_ctx.get()
        if ctx_correlation_id:
            query["correlation_id"] = ctx_correlation_id

    cursor = coleccion.find(query).sort("fecha", -1).limit(50)
    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)

    return logs


# 📧 Guardar log de correos en colección separada
async def guardar_log_correo(log: LogCorreo) -> Optional[str]:
    try:
        # 👇 Igual que con logs normales, añadimos correlation_id si está en contexto
        correlation_id = correlation_id_ctx.get()
        if correlation_id and "correlation_id" not in log.dict():
            log.correlation_id = correlation_id

        result = await mongo_db.logs_correos.insert_one(log.dict())
        return str(result.inserted_id)
    except PyMongoError as e:
        print(f"[Logger Correos] No se pudo guardar log de correo: {e}")
        return None


# 📧 Obtener últimos logs de correos
async def obtener_logs_correos(limit: int = 50) -> List[dict[Any, Any]]:
    coleccion = mongo_db.logs_correos
    cursor = coleccion.find().sort("fecha", -1).limit(limit)
    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    return logs
