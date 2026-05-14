from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.enums import EstadoOrganizacion


class OrganizacionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=120)
    email_contacto: EmailStr
    estado: EstadoOrganizacion = EstadoOrganizacion.activa

    @field_validator("nombre", "slug")
    @classmethod
    def normalizar_texto_obligatorio(cls, value: str) -> str:
        # Evita persistir campos obligatorios con solo espacios.
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacio.")
        return value

    @field_validator("slug")
    @classmethod
    def normalizar_slug(cls, value: str) -> str:
        # El slug se almacena en minusculas para garantizar unicidad consistente.
        return value.strip().lower()


class OrganizacionUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    email_contacto: EmailStr | None = None
    estado: EstadoOrganizacion | None = None

    @field_validator("nombre", "slug")
    @classmethod
    def normalizar_texto_opcional(cls, value: str | None) -> str | None:
        # Mantiene updates parciales sin aceptar strings vacios.
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacio.")
        return value

    @field_validator("slug")
    @classmethod
    def normalizar_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if value is not None else None


class OrganizacionEstadoUpdate(BaseModel):
    estado: EstadoOrganizacion


class OrganizacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    slug: str
    email_contacto: str
    estado: EstadoOrganizacion
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None
