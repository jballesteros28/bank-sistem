from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.utils import normalize_decimal


def _normalize_price(value: Any) -> Decimal:
    amount = normalize_decimal(value)
    if amount < Decimal("0.00"):
        raise ValueError("El precio mensual no puede ser negativo.")
    return amount


def _validate_limit(value: int | None) -> int | None:
    if value is not None and value <= 0:
        raise ValueError("El limite debe ser positivo o null.")
    return value


class PlanBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    codigo: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    descripcion: str | None = None
    precio_mensual: Decimal = Decimal("0.00")
    limite_usuarios: int | None = None
    limite_wallets: int | None = None
    limite_movimientos_mes: int | None = None
    permite_webhooks: bool = False
    permite_white_label: bool = False
    activo: bool = True

    @field_validator("nombre", "codigo", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return str(value).strip()

    @field_validator("codigo")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if value != value.lower() or " " in value:
            raise ValueError("El codigo debe estar en minusculas y sin espacios.")
        return value

    @field_validator("precio_mensual", mode="before")
    @classmethod
    def validate_price(cls, value: Any) -> Decimal:
        return _normalize_price(value)

    @field_validator("limite_usuarios", "limite_wallets", "limite_movimientos_mes")
    @classmethod
    def validate_limits(cls, value: int | None) -> int | None:
        return _validate_limit(value)


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    codigo: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    descripcion: str | None = None
    precio_mensual: Decimal | None = None
    limite_usuarios: int | None = None
    limite_wallets: int | None = None
    limite_movimientos_mes: int | None = None
    permite_webhooks: bool | None = None
    permite_white_label: bool | None = None
    activo: bool | None = None

    @field_validator("nombre", "codigo", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: str | None) -> str | None:
        return None if value is None else str(value).strip()

    @field_validator("codigo")
    @classmethod
    def validate_optional_code(cls, value: str | None) -> str | None:
        if value is not None and (value != value.lower() or " " in value):
            raise ValueError("El codigo debe estar en minusculas y sin espacios.")
        return value

    @field_validator("precio_mensual", mode="before")
    @classmethod
    def validate_optional_price(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return _normalize_price(value)

    @field_validator("limite_usuarios", "limite_wallets", "limite_movimientos_mes")
    @classmethod
    def validate_optional_limits(cls, value: int | None) -> int | None:
        return _validate_limit(value)


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    codigo: str
    descripcion: str | None = None
    precio_mensual: Decimal
    limite_usuarios: int | None = None
    limite_wallets: int | None = None
    limite_movimientos_mes: int | None = None
    permite_webhooks: bool
    permite_white_label: bool
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None


class PlanActualResponse(BaseModel):
    organizacion_id: UUID
    plan: PlanResponse


class CambiarPlanOrganizacionRequest(BaseModel):
    plan_id: UUID


class CambiarPlanOrganizacionResponse(BaseModel):
    organizacion_id: UUID
    plan: PlanResponse
    mensaje: str
