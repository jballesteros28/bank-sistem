from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.apps.organizaciones.schemas import OrganizacionResponse
from app.apps.usuarios.schemas import UsuarioResponse
from app.apps.wallets.schemas import WalletResponse


class OnboardingOrganizacionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email_contacto: EmailStr

    @field_validator("nombre", "slug", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return str(value).strip()

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.lower()


class OnboardingOwnerCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class OnboardingRegistroCreate(BaseModel):
    organizacion: OnboardingOrganizacionCreate
    owner: OnboardingOwnerCreate


class OnboardingRegistroResponse(BaseModel):
    organizacion: OrganizacionResponse
    owner: UsuarioResponse
    wallet_principal: WalletResponse

