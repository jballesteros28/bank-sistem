from pydantic import BaseModel, Field
from core.enums import TipoCuenta, EstadoCuenta

# 📝 Entrada para crear una nueva cuenta
class CuentaCreate(BaseModel):
    tipo: TipoCuenta = Field(..., description="Tipo de cuenta válida")

# 📤 Salida de datos de cuenta (lo que se devuelve al cliente)
class CuentaOut(BaseModel):
    id: int = Field(..., description="ID interno de la cuenta", example=1)
    numero: str = Field(..., description="Número único de la cuenta", example="2034521987")
    tipo: TipoCuenta = Field(..., description="Tipo de cuenta")
    saldo: float = Field(..., ge=0.0, description="Saldo actual de la cuenta")
    estado: EstadoCuenta = Field(..., description="Estado de la cuenta (activa, inactiva, congelada)")
    usuario_id: int = Field(..., description="ID del usuario dueño de la cuenta")

    class Config:
        from_attributes = True 
        
        
# 🧊 Entrada para cambiar estado de una cuenta
class CambiarEstadoCuenta(BaseModel):
    nuevo_estado: EstadoCuenta = Field(..., description="Nuevo estado: activa, inactiva o congelada")
