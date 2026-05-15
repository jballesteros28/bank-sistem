from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.shared.enums import EstadoWallet, MonedaWallet, OwnerTypeWallet, TipoWallet
from app.shared.utils import normalize_decimal


def _normalize_amount(value: Any, *, allow_zero: bool) -> Decimal | None:
    if value is None:
        return None
    amount = normalize_decimal(value)
    minimum = Decimal("0.00") if allow_zero else Decimal("0.01")
    if amount < minimum:
        raise ValueError("El monto no puede ser negativo." if allow_zero else "El monto debe ser mayor a 0.")
    return amount


TIPOS_WALLET_USUARIO = {TipoWallet.principal, TipoWallet.ahorro, TipoWallet.recompensas}
TIPOS_WALLET_ORGANIZACION = {
    TipoWallet.empresa,
    TipoWallet.operativa,
    TipoWallet.caja,
    TipoWallet.recompensas,
}


class WalletUsuarioCreate(BaseModel):
    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet = TipoWallet.principal
    moneda: MonedaWallet = MonedaWallet.ARS
    limite_operacion: Decimal | None = None
    es_principal: bool = False
    owner_type: OwnerTypeWallet = OwnerTypeWallet.usuario
    usuario_id: UUID | None = None
    organizacion_id: UUID | None = None
    organizacion_owner_id: UUID | None = None

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validate_limit(cls, value: Any) -> Decimal | None:
        return _normalize_amount(value, allow_zero=False)

    @model_validator(mode="after")
    def validate_owner(self) -> "WalletUsuarioCreate":
        if self.owner_type != OwnerTypeWallet.usuario:
            raise ValueError("El endpoint de wallets de usuario solo acepta owner_type usuario.")
        if self.organizacion_owner_id is not None:
            raise ValueError("Una wallet de usuario no puede tener organizacion_owner_id.")
        if self.tipo not in TIPOS_WALLET_USUARIO:
            raise ValueError("Tipo de wallet no permitido para usuario.")
        return self


class WalletOrganizacionCreate(BaseModel):
    alias: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoWallet = TipoWallet.empresa
    moneda: MonedaWallet = MonedaWallet.ARS
    limite_operacion: Decimal | None = None
    es_principal: bool = False
    owner_type: OwnerTypeWallet = OwnerTypeWallet.organizacion
    usuario_id: UUID | None = None
    organizacion_id: UUID | None = None
    organizacion_owner_id: UUID | None = None

    @field_validator("limite_operacion", mode="before")
    @classmethod
    def validate_limit(cls, value: Any) -> Decimal | None:
        return _normalize_amount(value, allow_zero=False)

    @model_validator(mode="after")
    def validate_owner(self) -> "WalletOrganizacionCreate":
        if self.owner_type != OwnerTypeWallet.organizacion:
            raise ValueError("El endpoint de wallets de organizacion solo acepta owner_type organizacion.")
        if self.usuario_id is not None:
            raise ValueError("Una wallet de organizacion no puede tener usuario_id.")
        if self.tipo not in TIPOS_WALLET_ORGANIZACION:
            raise ValueError("Tipo de wallet no permitido para organizacion.")
        return self


WalletCreate = WalletUsuarioCreate


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

    id: UUID
    alias: str | None = None
    tipo: TipoWallet
    estado: EstadoWallet
    moneda: MonedaWallet
    saldo: Decimal
    limite_operacion: Decimal | None = None
    es_principal: bool
    owner_type: OwnerTypeWallet
    usuario_id: UUID | None = None
    organizacion_owner_id: UUID | None = None
    organizacion_id: UUID
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None

    @field_validator("saldo", mode="before")
    @classmethod
    def normalize_balance(cls, value: Any) -> Decimal:
        return _normalize_amount(value, allow_zero=True) or Decimal("0.00")


class WalletBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saldo: Decimal
    moneda: MonedaWallet
    estado: EstadoWallet
    owner_type: OwnerTypeWallet
    usuario_id: UUID | None = None
    organizacion_owner_id: UUID | None = None
    organizacion_id: UUID

    @field_validator("saldo", mode="before")
    @classmethod
    def normalize_balance(cls, value: Any) -> Decimal:
        return _normalize_amount(value, allow_zero=True) or Decimal("0.00")
