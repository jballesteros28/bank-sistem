from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.wallet_enum import EstadoWallet, MonedaWallet, TipoWallet


_TIPO_CUENTA_A_WALLET: dict[str, str] = {
    "corriente": TipoWallet.empresa.value,
    "sueldo": TipoWallet.principal.value,
}


def _normalizar_decimal(valor: Any, *, permitir_cero: bool) -> Decimal | None:
    """Normaliza montos de wallet sin aceptar valores negativos."""
    if valor is None:
        return None

    decimal = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    decimal = decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    minimo = Decimal("0.00") if permitir_cero else Decimal("0.01")
    if decimal < minimo:
        raise ValueError("El monto debe ser mayor a 0." if not permitir_cero else "El monto no puede ser negativo.")
    return decimal


class WalletCreate(BaseModel):
    """Datos permitidos para crear una wallet sobre la tabla cuentas."""

    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet = Field(default=TipoWallet.principal)
    moneda: MonedaWallet = Field(default=MonedaWallet.ARS)
    limite_operacion: Decimal | None = Field(default=None)
    es_principal: bool = Field(default=False)
    usuario_id: int | None = Field(default=None, gt=0)

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validar_limite(cls, valor: Any) -> Decimal | None:
        return _normalizar_decimal(valor, permitir_cero=False)


class WalletUpdate(BaseModel):
    """Actualizacion parcial de metadatos de wallet."""

    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet | None = Field(default=None)
    moneda: MonedaWallet | None = Field(default=None)
    limite_operacion: Decimal | None = Field(default=None)
    es_principal: bool | None = Field(default=None)

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validar_limite(cls, valor: Any) -> Decimal | None:
        return _normalizar_decimal(valor, permitir_cero=False)


class WalletEstadoUpdate(BaseModel):
    estado: EstadoWallet = Field(..., description="Nuevo estado operativo de la wallet")


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: str | None = None
    tipo: TipoWallet
    estado: EstadoWallet
    moneda: MonedaWallet
    saldo: Decimal = Field(..., ge=0)
    limite_operacion: Decimal | None = None
    es_principal: bool
    usuario_id: int
    organizacion_id: UUID | None
    fecha_creacion: datetime

    @field_validator("tipo", mode="before")
    @classmethod
    def normalizar_tipo(cls, valor: Any) -> str:
        tipo = getattr(valor, "value", valor)
        return _TIPO_CUENTA_A_WALLET.get(str(tipo), str(tipo))

    @field_validator("estado", mode="before")
    @classmethod
    def normalizar_estado(cls, valor: Any) -> str:
        return str(getattr(valor, "value", valor))

    @field_validator("saldo", mode="before")
    @classmethod
    def normalizar_saldo(cls, valor: Any) -> Decimal:
        decimal = _normalizar_decimal(valor, permitir_cero=True)
        return decimal if decimal is not None else Decimal("0.00")

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def normalizar_limite(cls, valor: Any) -> Decimal | None:
        return _normalizar_decimal(valor, permitir_cero=False)


class WalletBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    saldo: Decimal = Field(..., ge=0)
    moneda: MonedaWallet
    estado: EstadoWallet
    usuario_id: int
    organizacion_id: UUID | None

    @field_validator("estado", mode="before")
    @classmethod
    def normalizar_estado(cls, valor: Any) -> str:
        return str(getattr(valor, "value", valor))

    @field_validator("saldo", mode="before")
    @classmethod
    def normalizar_saldo(cls, valor: Any) -> Decimal:
        decimal = _normalizar_decimal(valor, permitir_cero=True)
        return decimal if decimal is not None else Decimal("0.00")

