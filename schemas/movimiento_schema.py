from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.movimiento_enum import EstadoMovimiento, TipoMovimiento


def _normalizar_monto(valor: Any, *, debe_ser_positivo: bool = True) -> Decimal:
    decimal = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    decimal = decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if debe_ser_positivo and decimal <= Decimal("0.00"):
        raise ValueError("El monto debe ser mayor a 0.")
    return decimal


class MovimientoBaseCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    monto: Decimal = Field(..., description="Monto del movimiento")
    descripcion: str | None = Field(default=None, max_length=255)
    referencia_externa: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] | None = Field(default=None)

    @field_validator("monto", mode="before")
    @classmethod
    def validar_monto(cls, valor: Any) -> Decimal:
        return _normalizar_monto(valor)


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
    operacion: Literal["credito", "debito"] = Field(..., description="Tipo de ajuste administrativo")
    motivo: str = Field(..., min_length=3, max_length=255)


class MovimientoReversaCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    motivo_reversa: str = Field(..., min_length=3, max_length=255)
    referencia_externa: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] | None = Field(default=None)


class MovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    wallet_origen_id: int | None = Field(default=None)
    wallet_destino_id: int | None = Field(default=None)
    monto: Decimal
    tipo: TipoMovimiento
    estado: EstadoMovimiento
    descripcion: str | None = None
    referencia_externa: str | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_movimiento"),
    )
    movimiento_origen_id: UUID | None = None
    es_reversa: bool = False
    motivo_reversa: str | None = None
    organizacion_id: UUID | None = None
    fecha: datetime

    @field_validator("monto", mode="before")
    @classmethod
    def normalizar_monto(cls, valor: Any) -> Decimal:
        return _normalizar_monto(valor)

    @field_validator("tipo", mode="before")
    @classmethod
    def normalizar_tipo(cls, valor: Any) -> str:
        return str(getattr(valor, "value", valor))

    @field_validator("estado", mode="before")
    @classmethod
    def normalizar_estado(cls, valor: Any) -> str:
        estado = str(getattr(valor, "value", valor))
        return "aprobada" if estado == "completada" else estado

    @model_validator(mode="before")
    @classmethod
    def completar_wallet_aliases(cls, data: Any) -> Any:
        if hasattr(data, "cuenta_origen_id") and hasattr(data, "cuenta_destino_id"):
            return {
                "id": data.id,
                "wallet_origen_id": data.cuenta_origen_id,
                "wallet_destino_id": data.cuenta_destino_id,
                "monto": data.monto,
                "tipo": data.tipo,
                "estado": data.estado,
                "descripcion": data.descripcion,
                "referencia_externa": data.referencia_externa,
                "metadata_movimiento": data.metadata_movimiento,
                "movimiento_origen_id": data.movimiento_origen_id,
                "es_reversa": data.es_reversa,
                "motivo_reversa": data.motivo_reversa,
                "organizacion_id": data.organizacion_id,
                "fecha": data.fecha,
            }
        return data


class MovimientoListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movimientos: list[MovimientoResponse]
    total: int

