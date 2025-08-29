from pydantic import BaseModel, EmailStr, Field
from typing import Literal

# 🔐 Datos esperados al momento de registrar un nuevo usuario
class RegistroUsuario(BaseModel):
    nombre: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Nombre completo (mínimo 2 caracteres, máximo 100)"
    )
    email: EmailStr = Field(
        ..., 
        description="Correo electrónico válido (usado como identificador único)"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Contraseña segura (mínimo 8 caracteres, incluir letras y números)"
    )

# 🔐 Datos esperados al momento de hacer login
class LoginUsuario(BaseModel):
    email: EmailStr = Field(
        ..., 
        description="Correo electrónico con el que se registró el usuario"
    )
    password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="Contraseña del usuario (mínimo 8 caracteres)"
    )

# 📩 Respuesta del servidor después de un login exitoso
class TokenRespuesta(BaseModel):
    access_token: str = Field(..., description="Token de acceso tipo JWT")
    token_type: Literal["bearer"] = Field(default="bearer", description="Tipo de token")

# 🧾 Información del usuario extraída desde el token
class DatosUsuarioToken(BaseModel):
    id: int = Field(..., description="ID interno del usuario")
    email: EmailStr = Field(..., description="Email del usuario autenticado")
    nombre: str = Field(..., description="Nombre completo del usuario")
    rol: str = Field(..., description="Rol del usuario (cliente, admin, etc.)")

