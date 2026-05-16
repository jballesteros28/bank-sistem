from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


ALLOWED_API_KEY_SCOPES = {
    "wallets:read",
    "wallets:write",
    "movimientos:read",
    "movimientos:write",
    "usuarios:read",
    "usuarios:write",
    "webhooks:read",
    "webhooks:write",
}

ALLOWED_WEBHOOK_EVENTS = {
    "wallet.creada",
    "movimiento.creado",
    "movimiento.revertido",
    "pago_organizacion.creado",
    "notificacion.creada",
    "organizacion.suspendida",
}

WEBHOOK_DELIVERY_STATUSES = {"pendiente", "enviado", "fallido"}


def _validate_items(values: list[str], allowed: set[str], label: str) -> list[str]:
    normalized = [item.strip() for item in values if item.strip()]
    invalid = sorted(set(normalized) - allowed)
    if invalid:
        raise ValueError(f"{label} invalidos: {', '.join(invalid)}.")
    if not normalized:
        raise ValueError(f"Debe indicar al menos un {label[:-1]}.")
    return sorted(set(normalized))


class APIKeyCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    scopes: list[str] = Field(..., min_length=1)
    organizacion_id: UUID | None = None

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, values: list[str]) -> list[str]:
        return _validate_items(values, ALLOWED_API_KEY_SCOPES, "scopes")


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    nombre: str
    key_prefix: str
    scopes: list[str]
    activa: bool
    ultimo_uso_en: datetime | None = None
    fecha_creacion: datetime
    fecha_revocacion: datetime | None = None


class APIKeyCreateResponse(APIKeyResponse):
    api_key: str


class APIKeyRevokeResponse(BaseModel):
    id: UUID
    activa: bool
    fecha_revocacion: datetime
    mensaje: str


class WebhookEndpointCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    url: HttpUrl
    eventos: list[str] = Field(..., min_length=1)
    secret: str = Field(..., min_length=16, max_length=255)
    organizacion_id: UUID | None = None

    @field_validator("eventos")
    @classmethod
    def validate_events(cls, values: list[str]) -> list[str]:
        return _validate_items(values, ALLOWED_WEBHOOK_EVENTS, "eventos")


class WebhookEndpointUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    url: HttpUrl | None = None
    eventos: list[str] | None = Field(default=None, min_length=1)
    secret: str | None = Field(default=None, min_length=16, max_length=255)
    activo: bool | None = None

    @field_validator("eventos")
    @classmethod
    def validate_events(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return _validate_items(values, ALLOWED_WEBHOOK_EVENTS, "eventos")


class WebhookEndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    nombre: str
    url: str
    eventos: list[str]
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    webhook_endpoint_id: UUID
    evento: str
    payload: dict[str, Any]
    status: str
    status_code: int | None = None
    respuesta_body: str | None = None
    intentos: int
    error: str | None = None
    fecha_creacion: datetime
    fecha_ultimo_intento: datetime | None = None
