from pydantic import BaseModel, Field, field_validator
from core.enums import TipoCuenta, EstadoCuenta
from decimal import Decimal, ROUND_HALF_UP

# 📝 Entrada para crear una nueva cuenta
class CuentaCreate(BaseModel):
    tipo: TipoCuenta = Field(..., description="Tipo de cuenta válida")


# 📤 Salida de datos de cuenta (lo que se devuelve al cliente)
class CuentaOut(BaseModel):
    id: int = Field(..., description="ID interno de la cuenta", example=1)
    numero: str = Field(..., description="Número único de la cuenta", example="2034521987")
    tipo: TipoCuenta = Field(..., description="Tipo de cuenta")
    saldo: Decimal = Field(..., ge=0, description="Saldo actual de la cuenta con precisión monetaria")
    estado: EstadoCuenta = Field(..., description="Estado de la cuenta (activa, inactiva, congelada)")
    usuario_id: int = Field(..., description="ID del usuario dueño de la cuenta")

    class Config:
        from_attributes = True  

    # ✅ Validador: siempre redondear a 2 decimales
    @field_validator("saldo", mode="before")
    @classmethod
    def normalizar_saldo(cls, v: Decimal) -> Decimal:
        if isinstance(v, float):
            v = Decimal(str(v))
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# 🧊 Entrada para cambiar estado de una cuenta
class CambiarEstadoCuenta(BaseModel):
    nuevo_estado: EstadoCuenta = Field(..., description="Nuevo estado: activa, inactiva o congelada")


class ActualizarSaldo(BaseModel):
    saldo: Decimal = Field(..., ge=0, description="Nuevo saldo de la cuenta (>=0)")

    # ✅ Normalizar saldo a 2 decimales
    @field_validator("saldo", mode="before")
    @classmethod
    def normalizar_saldo(cls, v: Decimal) -> Decimal:
        if not isinstance(v, Decimal):
            v = Decimal(str(v))
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)