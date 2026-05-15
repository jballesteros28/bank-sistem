from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums import EstadoNotificacion, TipoNotificacion


class NotificacionCreate(BaseModel):
    usuario_id: int | None = Field(default=None, gt=0)
    organizacion_id: UUID | None = None
    tipo: TipoNotificacion = TipoNotificacion.generica
    asunto: str = Field(..., min_length=2, max_length=180)
    destinatario: EmailStr
    cuerpo: str = Field(..., min_length=1)


class NotificacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None = None
    organizacion_id: UUID | None = None
    tipo: TipoNotificacion
    estado: EstadoNotificacion
    asunto: str
    destinatario: EmailStr
    cuerpo: str
    fecha_creacion: datetime
    fecha_envio: datetime | None = None

