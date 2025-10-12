# schemas/notificacion.py
from pydantic import BaseModel, EmailStr, Field
from typing import Any, Dict
from core.enums import TipoNotificacion, EstadoNotificacion

# ─────────────────────────────────────────────
# Schema genérico (interno / logging / pruebas)
# ─────────────────────────────────────────────
class NotificationCreate(BaseModel):
    """
    Representa una notificación genérica para logging y pruebas internas.
    """
    to_email: EmailStr
    subject: str = Field(min_length=3, max_length=120)
    template: str = Field(description="Archivo HTML de plantilla, ej: 'bienvenida.html'")
    context: Dict[str, Any] = Field(default_factory=dict)
    tipo: TipoNotificacion = TipoNotificacion.GENERIC

class NotificationOut(BaseModel):
    """
    Respuesta estandarizada para cualquier notificación.
    Incluye ID de Mongo y estado actual.
    """
    id: str
    to_email: EmailStr
    subject: str
    tipo: TipoNotificacion
    status: EstadoNotificacion

# ─────────────────────────────────────────────
# Schemas especializados (para endpoints públicos)
# ─────────────────────────────────────────────
class BienvenidaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr

class TransferenciaExitosaIn(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=120)
    id_transaccion: int
    monto: float
    cuenta_origen: int
    cuenta_destino: int
    fecha: str = Field(description="Fecha legible o ISO, ej: 2025-09-18 12:34")
    descripcion: str = Field(min_length=3, max_length=500)

class ActividadSospechosaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    evento: str = Field(min_length=3, max_length=200)
    fecha: str
    ip: str = Field(min_length=3, max_length=64)

class ResetPasswordIn(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=120)
    codigo: str = Field(min_length=4, max_length=12, description="Código de recuperación")
