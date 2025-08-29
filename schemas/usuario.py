from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from core.enums import RolUsuario

# Datos comunes del usuario (compartido entre esquemas)
class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico válido")

# Esquema de salida (lo que se devuelve al frontend)
class UsuarioOut(UsuarioBase):
    id: int
    rol: str = Field(..., description="Rol asignado al usuario (cliente, admin, etc.)")
    es_activo: bool = Field(..., description="Indica si el usuario está habilitado")

    class Config:
        from_attributes = True  # Permite convertir desde modelos SQLAlchemy a este esquema

# Esquema para editar perfil (datos opcionales)
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

# Esquema para cambiar contraseña
class CambioPassword(BaseModel):
    actual: str = Field(..., min_length=6, max_length=128, description="Contraseña actual")
    nueva: str = Field(..., min_length=8, max_length=128, description="Nueva contraseña segura")
    
    

# 🎛️ Esquema para cambiar rol de un usuario
class CambiarRolUsuario(BaseModel):
    nuevo_rol: RolUsuario = Field(..., description="Nuevo rol del usuario (admin, cliente, soporte)")
