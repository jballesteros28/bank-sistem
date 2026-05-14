from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from schemas.organizacion_schema import OrganizacionResponse
from schemas.wallet_schema import WalletResponse


class OnboardingOrganizacionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email_contacto: EmailStr

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre es obligatorio.")
        return value

    @field_validator("slug", mode="before")
    @classmethod
    def normalizar_slug(cls, value: str) -> str:
        # El slug publico del tenant se normaliza antes de validar formato.
        return str(value).strip().lower()


class OnboardingOwnerCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre del owner es obligatorio.")
        return value


class OnboardingRegistroCreate(BaseModel):
    organizacion: OnboardingOrganizacionCreate
    owner: OnboardingOwnerCreate


class OnboardingOwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    rol: str
    organizacion_id: UUID


class OnboardingRegistroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organizacion: OrganizacionResponse
    owner: OnboardingOwnerResponse
    wallet_principal: WalletResponse

