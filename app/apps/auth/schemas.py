from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.enums import RolUsuario


class RegistroUsuario(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    organizacion_slug: str = Field(..., min_length=2, max_length=120)

    @field_validator("organizacion_slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class LoginUsuario(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class DatosUsuarioToken(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    organizacion_id: UUID | None = None

