from pydantic import BaseModel, EmailStr

# Datos esperados al momento de registrar un nuevo usuario
class RegistroUsuario(BaseModel):
    nombre: str                  # Nombre completo del usuario
    email: EmailStr              # Correo electrónico (validado)
    password: str                # Contraseña en texto plano

# Datos esperados al momento de hacer login
class LoginUsuario(BaseModel):
    email: EmailStr              # Solo se necesita el email
    password: str                # Y la contraseña para autenticarse

# Respuesta del servidor después de un login exitoso
class TokenRespuesta(BaseModel):
    access_token: str            # Token JWT emitido
    token_type: str = "bearer"   # Tipo de token (Bearer por convención)

# Información del usuario extraída desde el token
class DatosUsuarioToken(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: str
