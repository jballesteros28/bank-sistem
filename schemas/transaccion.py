from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
from core.enums import TipoTransaccion, EstadoTransaccion


# 📝 Esquema de entrada: crear una nueva transacción
class TransaccionCreate(BaseModel):
    """
    Esquema para la creación de una transacción.
    Valida que el monto sea positivo y lo normaliza a dos decimales.
    """
    cuenta_destino_id: int = Field(..., gt=0, description="ID de la cuenta destino")
    monto: Decimal = Field(..., gt=0, description="Monto a transferir (debe ser mayor a 0)")
    tipo: TipoTransaccion = Field(
        default=TipoTransaccion.transferencia,
        description="Tipo de transacción"
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Descripción opcional de la transacción"
    )

    # ✅ Normalizar monto a 2 decimales, incluso si es int o float
    @field_validator("monto", mode="before")
    @classmethod
    def normalizar_monto(cls, v: Decimal | float | int) -> Decimal:
        """
        Convierte cualquier valor numérico (int, float, Decimal) a Decimal con 2 decimales.
        """
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        elif not isinstance(v, Decimal):
            raise TypeError("El monto debe ser un número válido.")
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# 📤 Esquema de salida: devolver una transacción
class TransaccionOut(BaseModel):
    """
    Esquema de salida para mostrar una transacción completa.
    Incluye información sobre origen, destino, estado y monto.
    """
    id: int = Field(..., description="ID de la transacción")
    cuenta_origen_id: int = Field(..., description="ID de la cuenta que envió el dinero")
    cuenta_destino_id: int = Field(..., description="ID de la cuenta que recibió el dinero")
    monto: Decimal = Field(..., description="Monto transferido con precisión monetaria")
    tipo: TipoTransaccion = Field(..., description="Tipo de transacción")
    estado: EstadoTransaccion = Field(..., description="Estado de la transacción")
    fecha: datetime = Field(..., description="Fecha y hora de ejecución")
    descripcion: Optional[str] = Field(default=None, max_length=255)

    class Config:
        from_attributes = True  # Permite usar model_validate con ORM

    # ✅ Normalizar monto en salida (por coherencia)
    @field_validator("monto", mode="before")
    @classmethod
    def normalizar_monto(cls, v: Decimal | float | int) -> Decimal:
        """
        Convierte y normaliza el monto a Decimal(2) para garantizar consistencia.
        """
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        elif not isinstance(v, Decimal):
            raise TypeError("El monto debe ser un número válido.")
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
