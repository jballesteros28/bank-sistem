from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums import EstadoWallet, MonedaWallet, TipoWallet
from app.shared.utils import normalize_decimal


def _normalize_amount(value: Any, *, allow_zero: bool) -> Decimal | None:
    if value is None:
        return None
    amount = normalize_decimal(value)
    minimum = Decimal("0.00") if allow_zero else Decimal("0.01")
    if amount < minimum:
        raise ValueError("El monto no puede ser negativo." if allow_zero else "El monto debe ser mayor a 0.")
    return amount


class WalletCreate(BaseModel):
    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet = TipoWallet.principal
    moneda: MonedaWallet = MonedaWallet.ARS
    limite_operacion: Decimal | None = None
    es_principal: bool = False
    usuario_id: int | None = Field(default=None, gt=0)
    organizacion_id: UUID | None = None

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validate_limit(cls, value: Any) -> Decimal | None:
        return _normalize_amount(value, allow_zero=False)


class WalletUpdate(BaseModel):
    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet | None = None
    limite_operacion: Decimal | None = None
    es_principal: bool | None = None

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validate_limit(cls, value: Any) -> Decimal | None:
        return _normalize_amount(value, allow_zero=False)


class WalletEstadoUpdate(BaseModel):
    estado: EstadoWallet


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: str | None = None
    tipo: TipoWallet
    estado: EstadoWallet
    moneda: MonedaWallet
    saldo: Decimal
    limite_operacion: Decimal | None = None
    es_principal: bool
    usuario_id: int
    organizacion_id: UUID
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None

    @field_validator("saldo", mode="before")
    @classmethod
    def normalize_balance(cls, value: Any) -> Decimal:
        return _normalize_amount(value, allow_zero=True) or Decimal("0.00")


class WalletBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    saldo: Decimal
    moneda: MonedaWallet
    estado: EstadoWallet
    usuario_id: int
    organizacion_id: UUID

    @field_validator("saldo", mode="before")
    @classmethod
    def normalize_balance(cls, value: Any) -> Decimal:
        return _normalize_amount(value, allow_zero=True) or Decimal("0.00")

