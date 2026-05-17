from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.apps.movimientos.schemas import MovimientoResponse
from app.shared.enums import EstadoReglaRecompensa, MonedaRecompensa, TipoRecompensa
from app.shared.utils import normalize_decimal


def _normalize_optional_amount(value: Any, *, allow_zero: bool) -> Decimal | None:
    if value is None:
        return None
    amount = normalize_decimal(value)
    minimum = Decimal("0.00") if allow_zero else Decimal("0.01")
    if amount < minimum:
        raise ValueError("El monto no puede ser negativo." if allow_zero else "El monto debe ser mayor a 0.")
    return amount


def _normalize_positive_amount(value: Any) -> Decimal:
    amount = normalize_decimal(value)
    if amount <= Decimal("0.00"):
        raise ValueError("El monto debe ser mayor a 0.")
    return amount


def _validate_percentage(value: Any) -> Decimal | None:
    if value is None:
        return None
    percentage = normalize_decimal(value)
    if percentage <= Decimal("0.00") or percentage > Decimal("100.00"):
        raise ValueError("El porcentaje debe ser mayor a 0 y menor o igual a 100.")
    return percentage


class ReglaRecompensaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo: TipoRecompensa
    porcentaje_cashback: Decimal | None = None
    monto_fijo: Decimal | None = None
    moneda_recompensa: MonedaRecompensa = MonedaRecompensa.PUNTOS
    monto_minimo_compra: Decimal | None = None
    monto_maximo_recompensa: Decimal | None = None
    acumulable: bool = True
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None

    @field_validator("porcentaje_cashback", mode="before")
    @classmethod
    def validate_percentage(cls, value: Any) -> Decimal | None:
        return _validate_percentage(value)

    @field_validator("monto_fijo", "monto_maximo_recompensa", mode="before")
    @classmethod
    def validate_positive_optional_amount(cls, value: Any) -> Decimal | None:
        return _normalize_optional_amount(value, allow_zero=False)

    @field_validator("monto_minimo_compra", mode="before")
    @classmethod
    def validate_minimum_amount(cls, value: Any) -> Decimal | None:
        return _normalize_optional_amount(value, allow_zero=True)

    @model_validator(mode="after")
    def validate_rule(self) -> "ReglaRecompensaCreate":
        if self.porcentaje_cashback is None and self.monto_fijo is None:
            raise ValueError("Debe informar porcentaje_cashback o monto_fijo.")
        if self.fecha_inicio is not None and self.fecha_fin is not None and self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio.")
        return self


class ReglaRecompensaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo: TipoRecompensa | None = None
    estado: EstadoReglaRecompensa | None = None
    porcentaje_cashback: Decimal | None = None
    monto_fijo: Decimal | None = None
    moneda_recompensa: MonedaRecompensa | None = None
    monto_minimo_compra: Decimal | None = None
    monto_maximo_recompensa: Decimal | None = None
    acumulable: bool | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None

    @field_validator("porcentaje_cashback", mode="before")
    @classmethod
    def validate_percentage(cls, value: Any) -> Decimal | None:
        return _validate_percentage(value)

    @field_validator("monto_fijo", "monto_maximo_recompensa", mode="before")
    @classmethod
    def validate_positive_optional_amount(cls, value: Any) -> Decimal | None:
        return _normalize_optional_amount(value, allow_zero=False)

    @field_validator("monto_minimo_compra", mode="before")
    @classmethod
    def validate_minimum_amount(cls, value: Any) -> Decimal | None:
        return _normalize_optional_amount(value, allow_zero=True)

    @model_validator(mode="after")
    def validate_dates(self) -> "ReglaRecompensaUpdate":
        if self.fecha_inicio is not None and self.fecha_fin is not None and self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio.")
        return self


class ReglaRecompensaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    nombre: str
    descripcion: str | None = None
    tipo: TipoRecompensa
    estado: EstadoReglaRecompensa
    porcentaje_cashback: Decimal | None = None
    monto_fijo: Decimal | None = None
    moneda_recompensa: MonedaRecompensa
    monto_minimo_compra: Decimal | None = None
    monto_maximo_recompensa: Decimal | None = None
    acumulable: bool
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None


class SimularRecompensaRequest(BaseModel):
    monto_compra: Decimal
    regla_id: UUID | None = None
    tipo: TipoRecompensa | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("monto_compra", mode="before")
    @classmethod
    def validate_purchase_amount(cls, value: Any) -> Decimal:
        return _normalize_positive_amount(value)


class SimularRecompensaResponse(BaseModel):
    aplica: bool
    regla_id: UUID | None = None
    nombre_regla: str | None = None
    monto_compra: Decimal
    monto_recompensa: Decimal
    moneda_recompensa: MonedaRecompensa | None = None
    motivo: str


class AplicarRecompensaRequest(BaseModel):
    usuario_id: UUID
    wallet_destino_id: UUID
    monto_compra: Decimal
    regla_id: UUID | None = None
    referencia_externa: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] | None = None

    @field_validator("monto_compra", mode="before")
    @classmethod
    def validate_purchase_amount(cls, value: Any) -> Decimal:
        return _normalize_positive_amount(value)


class AplicacionRecompensaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    regla_id: UUID
    usuario_id: UUID
    wallet_destino_id: UUID
    movimiento_id: UUID | None = None
    monto_compra: Decimal
    monto_recompensa: Decimal
    moneda_recompensa: MonedaRecompensa
    referencia_externa: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_aplicacion")
    fecha_creacion: datetime


class AplicarRecompensaResponse(BaseModel):
    aplicacion: AplicacionRecompensaResponse
    movimiento: MovimientoResponse
