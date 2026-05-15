from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.shared.enums import EstadoOrganizacion


ALLOWED_BRANDING_CURRENCIES = {"ARS", "USD", "USDT", "PUNTOS"}
HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
TIMEZONE_PATTERN = re.compile(r"^(?:UTC|[A-Za-z0-9_+\-]+(?:/[A-Za-z0-9_+\-]+)+)$")


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _validate_hex_color(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is not None and not HEX_COLOR_PATTERN.fullmatch(cleaned):
        raise ValueError("El color debe tener formato HEX valido.")
    return cleaned


def _validate_subdomain(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    cleaned = cleaned.lower()
    if not SUBDOMAIN_PATTERN.fullmatch(cleaned):
        raise ValueError("El subdominio debe usar minusculas, numeros y guiones.")
    return cleaned


def _validate_custom_domain(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    cleaned = cleaned.lower()
    if "://" in cleaned or not DOMAIN_PATTERN.fullmatch(cleaned):
        raise ValueError("El dominio personalizado no tiene un formato valido.")
    return cleaned


def _validate_logo_url(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("logo_url debe ser una URL http o https valida.")
    return cleaned


def _validate_currency(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    cleaned = cleaned.upper()
    if cleaned not in ALLOWED_BRANDING_CURRENCIES:
        raise ValueError("moneda_default debe ser ARS, USD, USDT o PUNTOS.")
    return cleaned


def _validate_timezone(value: str | None) -> str | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    if not TIMEZONE_PATTERN.fullmatch(cleaned):
        raise ValueError("timezone no tiene un formato valido.")
    return cleaned


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
    plan_id: UUID | None = None
    estado: EstadoOrganizacion
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None = None


class OrganizacionBrandingUpdate(BaseModel):
    nombre_comercial: str | None = Field(default=None, max_length=150)
    logo_url: str | None = Field(default=None, max_length=500)
    color_primario: str | None = None
    color_secundario: str | None = None
    subdominio: str | None = Field(default=None, max_length=120)
    dominio_personalizado: str | None = Field(default=None, max_length=255)
    moneda_default: str | None = None
    timezone: str | None = Field(default=None, max_length=80)
    permite_white_label_activo: bool | None = None

    @field_validator("nombre_comercial", mode="before")
    @classmethod
    def normalize_nombre_comercial(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)

    @field_validator("logo_url", mode="before")
    @classmethod
    def validate_logo_url(cls, value: str | None) -> str | None:
        return _validate_logo_url(value)

    @field_validator("color_primario", "color_secundario", mode="before")
    @classmethod
    def validate_hex_colors(cls, value: str | None) -> str | None:
        return _validate_hex_color(value)

    @field_validator("subdominio", mode="before")
    @classmethod
    def validate_subdomain(cls, value: str | None) -> str | None:
        return _validate_subdomain(value)

    @field_validator("dominio_personalizado", mode="before")
    @classmethod
    def validate_custom_domain(cls, value: str | None) -> str | None:
        return _validate_custom_domain(value)

    @field_validator("moneda_default", mode="before")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        return _validate_currency(value)

    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        return _validate_timezone(value)


class OrganizacionBrandingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    nombre_comercial: str | None = None
    logo_url: str | None = None
    color_primario: str | None = None
    color_secundario: str | None = None
    subdominio: str | None = None
    dominio_personalizado: str | None = None
    moneda_default: str
    timezone: str
    permite_white_label_activo: bool
    plan_id: UUID | None = None
