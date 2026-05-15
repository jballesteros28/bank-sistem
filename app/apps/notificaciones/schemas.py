from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums import CanalNotificacion, TipoNotificacion


class NotificacionCreate(BaseModel):
    organizacion_id: UUID
    usuario_id: UUID | None = None
    tipo: TipoNotificacion
    canal: CanalNotificacion = CanalNotificacion.interna
    titulo: str = Field(..., min_length=2, max_length=180)
    mensaje: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None


class NotificacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    usuario_id: UUID | None = None
    tipo: TipoNotificacion
    canal: CanalNotificacion
    titulo: str
    mensaje: str
    metadata_notificacion: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    leida: bool
    enviada: bool
    error_envio: str | None = None
    fecha_creacion: datetime
    fecha_lectura: datetime | None = None
    fecha_envio: datetime | None = None


class NotificacionListResponse(BaseModel):
    items: list[NotificacionResponse]
    total: int
    no_leidas: int


class NotificacionMarcarLeidaRequest(BaseModel):
    leida: bool = True


class EmailTemplateContext(BaseModel):
    organizacion_id: UUID
    destinatario: EmailStr
    asunto: str
    titulo: str
    mensaje: str
    nombre_organizacion: str
    color_primario: str = "#0f766e"
    logo_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
