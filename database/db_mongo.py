import motor.motor_asyncio
from core.config import settings

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB]

# 📦 Obtener la colección de logs de MongoDB
def get_logs_collection():
    return mongo_db.get_collection("logs")
