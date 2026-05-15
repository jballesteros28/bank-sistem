from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.apps.notificaciones.services import notificar_onboarding_exitoso
from app.apps.onboarding.schemas import OnboardingRegistroCreate, OnboardingRegistroResponse
from app.apps.onboarding.services import registrar_organizacion_con_owner
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post(
    "/registro-organizacion",
    response_model=ApiResponse[OnboardingRegistroResponse],
    status_code=status.HTTP_201_CREATED,
)
def post_registro_organizacion(
    datos: OnboardingRegistroCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ApiResponse[OnboardingRegistroResponse]:
    resultado = registrar_organizacion_con_owner(datos, db)
    notificar_onboarding_exitoso(resultado, db, background_tasks)
    return ok(resultado, "Organizacion registrada correctamente.")
