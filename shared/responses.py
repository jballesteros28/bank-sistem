from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Envelope estandar para respuestas exitosas de la API nueva."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    data: T | None = None


class ApiErrorResponse(BaseModel):
    """Envelope documentado para errores de negocio y validacion."""

    success: bool = False
    message: str
    error_code: str | None = None
    details: dict | list | None = None


def ok(data: T, message: str = "Operacion realizada correctamente.") -> ApiResponse[T]:
    """Construye una respuesta exitosa uniforme sin repetir estructura."""
    return ApiResponse(success=True, message=message, data=data)

