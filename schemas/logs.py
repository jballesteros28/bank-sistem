# schemas/logs.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LogMongoOut(BaseModel):
    """
    Esquema de salida para logs generales (colección: logs).
    Mapea _id -> id y tolera campos extra que vengan desde Mongo.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    evento: str
    mensaje: str
    nivel: str = "INFO"
    usuario_id: Optional[int] = None
    endpoint: Optional[str] = None
    ip: Optional[str] = None
    fecha: datetime


class LogCorreoOut(BaseModel):
    """
    Esquema de salida para logs de correos (colección: logs_correos).
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    destinatario: str
    asunto: str
    template: str
    estado: str            # "ENVIADO" | "ERROR"
    error: Optional[str] = None
    fecha: datetime
