from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums import EstadoMovimiento, TipoMovimiento
from app.shared.utils import normalize_decimal


def _positive_amount(value: Any) -> Decimal:
    amount = normalize_decimal(value)
    if amount <= Decimal("0.00"):
        raise ValueError("El monto debe ser mayor a 0.")
    return amount


class MovimientoBaseCreate(BaseModel):
    monto: Decimal
    descripcion: str | None = Field(default=None, max_length=255)
    referencia_externa: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def validate_amount(cls, value: Any) -> Decimal:
        return _positive_amount(value)


class MovimientoDepositoCreate(MovimientoBaseCreate):
    wallet_destino_id: int = Field(..., gt=0)


class MovimientoRetiroCreate(MovimientoBaseCreate):
    wallet_origen_id: int = Field(..., gt=0)


class MovimientoTransferenciaCreate(MovimientoBaseCreate):
    wallet_origen_id: int = Field(..., gt=0)
    wallet_destino_id: int = Field(..., gt=0)


class MovimientoPagoCreate(MovimientoTransferenciaCreate):
    pass


class MovimientoCashbackCreate(MovimientoBaseCreate):
    wallet_destino_id: int = Field(..., gt=0)


class MovimientoAjusteAdminCreate(MovimientoBaseCreate):
    wallet_destino_id: int = Field(..., gt=0)
    operacion: Literal["credito", "debito"]
    motivo: str = Field(..., min_length=3, max_length=255)


class MovimientoReversaCreate(BaseModel):
    motivo_reversa: str = Field(..., min_length=3, max_length=255)
    referencia_externa: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] | None = None


class MovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_origen_id: int
    wallet_destino_id: int
    monto: Decimal
    tipo: TipoMovimiento
    estado: EstadoMovimiento
    descripcion: str | None = None
    referencia_externa: str | None = None
    metadata_movimiento: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    movimiento_origen_id: int | None = None
    es_reversa: bool
    motivo_reversa: str | None = None
    organizacion_id: UUID
    fecha: datetime

    @field_validator("monto", mode="before")
    @classmethod
    def normalize_amount(cls, value: Any) -> Decimal:
        return normalize_decimal(value)

