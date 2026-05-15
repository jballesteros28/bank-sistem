from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.shared.enums import EstadoOrganizacion


class OrganizacionCreate(BaseModel):
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


class OrganizacionUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    email_contacto: EmailStr | None = None
    estado: EstadoOrganizacion | None = None


class OrganizacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    slug: str
    email_contacto: EmailStr
    estado: EstadoOrganizacion
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None

