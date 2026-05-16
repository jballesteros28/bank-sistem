from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


AuditActorTipo = Literal["usuario", "api_key", "sistema"]


class AuditLogCreate(BaseModel):
    evento: str = Field(..., min_length=2, max_length=120)
    mensaje: str = Field(..., min_length=2, max_length=500)
    nivel: str = Field(default="INFO", max_length=20)
    actor_tipo: AuditActorTipo | None = None
    actor_usuario_id: UUID | None = None
    actor_api_key_id: UUID | None = None
    organizacion_id: UUID | None = None
    endpoint: str | None = None
    ip: str | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalizar_actor_tipo(self) -> "AuditLogCreate":
        if self.actor_tipo is None:
            if self.actor_api_key_id is not None:
                self.actor_tipo = "api_key"
            elif self.actor_usuario_id is not None:
                self.actor_tipo = "usuario"
            else:
                self.actor_tipo = "sistema"
        return self


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evento: str
    mensaje: str
    nivel: str
    actor_tipo: str
    actor_usuario_id: UUID | None = None
    actor_api_key_id: UUID | None = None
    organizacion_id: UUID | None = None
    endpoint: str | None = None
    ip: str | None = None
    metadata_log: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    fecha: datetime
