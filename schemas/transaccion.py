from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from core.enums import EstadoTransaccion, TipoTransaccion


class TransaccionCreate(BaseModel):
    """Entrada compatible con cuentas historicas y aliases wallet_*."""

    model_config = ConfigDict(populate_by_name=True)

    cuenta_destino_id: int = Field(
        ...,
        gt=0,
        validation_alias=AliasChoices("cuenta_destino_id", "wallet_destino_id"),
        description="ID de la cuenta/wallet destino",
    )
    monto: Decimal = Field(..., gt=0, description="Monto a transferir (debe ser mayor a 0)")
    tipo: TipoTransaccion = Field(
        default=TipoTransaccion.transferencia,
        description="Tipo de transaccion",
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Descripcion opcional de la transaccion",
    )

    @field_validator("monto", mode="before")
    @classmethod
    def normalizar_monto(cls, v: Decimal | float | int) -> Decimal:
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        elif not isinstance(v, Decimal):
            raise TypeError("El monto debe ser un numero valido.")
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TransaccionOut(BaseModel):
    """Salida de transaccion con campos historicos y aliases SaaS de wallet."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID de la transaccion")
    cuenta_origen_id: int = Field(..., description="ID de la cuenta que envio el dinero")
    cuenta_destino_id: int = Field(..., description="ID de la cuenta que recibio el dinero")
    wallet_origen_id: int | None = Field(default=None, description="Alias de cuenta_origen_id")
    wallet_destino_id: int | None = Field(default=None, description="Alias de cuenta_destino_id")
    monto: Decimal = Field(..., description="Monto transferido con precision monetaria")
    tipo: TipoTransaccion = Field(..., description="Tipo de transaccion")
    estado: EstadoTransaccion = Field(..., description="Estado de la transaccion")
    fecha: datetime = Field(..., description="Fecha y hora de ejecucion")
    descripcion: Optional[str] = Field(default=None, max_length=255)

    @field_validator("monto", mode="before")
    @classmethod
    def normalizar_monto(cls, v: Decimal | float | int) -> Decimal:
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        elif not isinstance(v, Decimal):
            raise TypeError("El monto debe ser un numero valido.")
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @model_validator(mode="after")
    def completar_alias_wallet(self) -> "TransaccionOut":
        self.wallet_origen_id = self.cuenta_origen_id
        self.wallet_destino_id = self.cuenta_destino_id
        return self
