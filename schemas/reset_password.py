# schemas/reset_password.py
from pydantic import BaseModel, EmailStr, Field

# ══════════════════════════════════════════════
# 📌 Esquema para solicitar un reset
# ══════════════════════════════════════════════
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# ══════════════════════════════════════════════
# 📌 Esquema para validar un código de reset
# ══════════════════════════════════════════════
class ValidateResetRequest(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=12)


# ══════════════════════════════════════════════
# 📌 Esquema para confirmar el reset con nueva contraseña
# ══════════════════════════════════════════════
class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=12)
    nueva_password: str = Field(min_length=8, max_length=64)


# ══════════════════════════════════════════════
# 📌 Respuesta estándar para operaciones de reset
# ══════════════════════════════════════════════
class ResetPasswordResponse(BaseModel):
    msg: str
