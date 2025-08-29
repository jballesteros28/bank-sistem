from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

# 📝 Entrada para crear una nueva transacción
class TransaccionCreate(BaseModel):
    cuenta_destino_id: int = Field(..., gt=0, description="ID de la cuenta destino")
    monto: float = Field(..., gt=0.0, description="Monto a transferir (debe ser mayor a 0)")
    tipo: Literal["transferencia"] = Field(
        default="transferencia",
        description="Tipo de transacción (actualmente solo se permite transferencia)"
    )

# 📤 Salida de una transacción
class TransaccionOut(BaseModel):
    id: int = Field(..., description="ID de la transacción")
    cuenta_origen_id: int = Field(..., description="ID de la cuenta que envió el dinero")
    cuenta_destino_id: int = Field(..., description="ID de la cuenta que recibió el dinero")
    monto: float = Field(..., description="Monto transferido")
    tipo: str = Field(..., description="Tipo de transacción")
    estado: str = Field(..., description="Estado de la transacción")
    fecha: datetime = Field(..., description="Fecha y hora de ejecución")

    class Config:
        from_attributes = True  # Equivalente a orm_mode en Pydantic v2
