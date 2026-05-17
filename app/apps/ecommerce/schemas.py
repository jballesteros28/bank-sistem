from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.apps.movimientos.schemas import MovimientoResponse
from app.apps.recompensas.schemas import AplicacionRecompensaResponse
from app.shared.utils import normalize_decimal, normalize_email


class EcommerceOrderPaidRequest(BaseModel):
    proveedor: str = Field(default="generic", min_length=1, max_length=60)
    external_order_id: str = Field(..., min_length=1, max_length=160)
    customer_email: EmailStr
    customer_name: str | None = Field(default=None, max_length=120)
    amount: Decimal
    currency: str = Field(default="ARS", min_length=2, max_length=20)
    metadata: dict[str, Any] | None = None

    @field_validator("proveedor", mode="before")
    @classmethod
    def normalize_provider(cls, value: Any) -> str:
        return str(value or "generic").strip().lower()

    @field_validator("external_order_id", mode="before")
    @classmethod
    def normalize_external_order_id(cls, value: Any) -> str:
        return str(value).strip()

    @field_validator("customer_email", mode="after")
    @classmethod
    def normalize_customer_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))

    @field_validator("customer_name", mode="before")
    @classmethod
    def normalize_customer_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Any) -> Decimal:
        amount = normalize_decimal(value)
        if amount <= Decimal("0.00"):
            raise ValueError("El monto debe ser mayor a 0.")
        return amount

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: Any) -> str:
        return str(value or "ARS").strip().upper()


class EcommerceOrderEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizacion_id: UUID
    proveedor: str
    external_order_id: str
    customer_email: str
    customer_name: str | None = None
    amount: Decimal
    currency: str
    status: str
    raw_payload: dict[str, Any] | None = None
    procesado: bool
    recompensa_aplicada_id: UUID | None = None
    error_procesamiento: str | None = None
    fecha_creacion: datetime
    fecha_procesamiento: datetime | None = None


class EcommerceOrderPaidResponse(BaseModel):
    event: EcommerceOrderEventResponse
    recompensa_aplicada: AplicacionRecompensaResponse | None = None
    movimiento: MovimientoResponse | None = None
    mensaje: str
