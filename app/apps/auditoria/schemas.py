from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    evento: str = Field(..., min_length=2, max_length=120)
    mensaje: str = Field(..., min_length=2, max_length=500)
    nivel: str = Field(default="INFO", max_length=20)
    actor_usuario_id: UUID | None = None
    organizacion_id: UUID | None = None
    endpoint: str | None = None
    ip: str | None = None
    metadata: dict[str, Any] | None = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evento: str
    mensaje: str
    nivel: str
    actor_usuario_id: UUID | None = None
    organizacion_id: UUID | None = None
    endpoint: str | None = None
    ip: str | None = None
    metadata_log: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    fecha: datetime
