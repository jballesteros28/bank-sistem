from models.log import LogMongo
from database.db_mongo import mongo_db, get_logs_collection
from pymongo.errors import PyMongoError
from typing import List, Optional
from datetime import datetime

# 📝 Guardar log en la colección de MongoDB
async def guardar_log(log: LogMongo):
    try:
        await mongo_db.logs.insert_one(log.__dict__)
    except PyMongoError as e:
        # Fallback: imprimir si falla Mongo
        print(f"[Logger MongoDB] No se pudo guardar el log: {e}")
        
        
# 📄 Obtener logs desde MongoDB con filtros opcionales
async def obtener_logs(
    evento: Optional[str] = None,
    nivel: Optional[str] = None
) -> List[dict]:
    coleccion = get_logs_collection()

    # 🎯 Filtros dinámicos
    query = {}
    if evento:
        query["evento"] = evento
    if nivel:
        query["nivel"] = nivel

    # 🔄 Obtener los últimos 50 logs (orden descendente por fecha)
    cursor = coleccion.find(query).sort("fecha", -1).limit(50)
    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])  # Convertir ObjectId a string para respuesta JSON
        logs.append(log)

    return logs
        

