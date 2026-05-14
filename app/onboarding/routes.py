from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from schemas.onboarding_schema import OnboardingRegistroCreate, OnboardingRegistroResponse
from services.onboarding_service import registrar_organizacion_con_owner
from shared.responses import ApiResponse, ok


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post(
    "/registro-organizacion",
    response_model=ApiResponse[OnboardingRegistroResponse],
    status_code=status.HTTP_201_CREATED,
)
def registrar_organizacion(
    datos: OnboardingRegistroCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[OnboardingRegistroResponse]:
    """Registra una organizacion SaaS con owner y wallet principal inicial."""
    resultado = registrar_organizacion_con_owner(datos, db)
    return ok(resultado, "Organizacion registrada correctamente.")

