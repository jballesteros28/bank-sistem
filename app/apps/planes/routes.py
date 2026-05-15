from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.planes.schemas import (
    CambiarPlanOrganizacionRequest,
    CambiarPlanOrganizacionResponse,
    PlanActualResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
)
from app.apps.planes.services import (
    actualizar_plan,
    cambiar_plan_organizacion,
    crear_plan,
    listar_planes,
    obtener_plan_actual_de_organizacion,
    obtener_plan_por_id,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/planes", tags=["Planes SaaS"])


@router.post("", response_model=ApiResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
def post_plan(
    datos: PlanCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PlanResponse]:
    return ok(crear_plan(datos, current_user, db), "Plan creado correctamente.")


@router.get("", response_model=ApiResponse[list[PlanResponse]])
def get_planes(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[PlanResponse]]:
    return ok(listar_planes(current_user, db), "Planes obtenidos correctamente.")


@router.get("/organizacion/actual", response_model=ApiResponse[PlanActualResponse])
def get_plan_actual(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PlanActualResponse]:
    return ok(
        obtener_plan_actual_de_organizacion(current_user, db, organizacion_id),
        "Plan actual obtenido correctamente.",
    )


@router.patch(
    "/organizaciones/{organizacion_id}/cambiar-plan",
    response_model=ApiResponse[CambiarPlanOrganizacionResponse],
)
def patch_plan_organizacion(
    organizacion_id: UUID,
    datos: CambiarPlanOrganizacionRequest,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[CambiarPlanOrganizacionResponse]:
    return ok(
        cambiar_plan_organizacion(organizacion_id, datos.plan_id, current_user, db),
        "Plan de organizacion actualizado correctamente.",
    )


@router.get("/{plan_id}", response_model=ApiResponse[PlanResponse])
def get_plan(
    plan_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PlanResponse]:
    return ok(obtener_plan_por_id(plan_id, current_user, db), "Plan obtenido correctamente.")


@router.patch("/{plan_id}", response_model=ApiResponse[PlanResponse])
def patch_plan(
    plan_id: UUID,
    datos: PlanUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PlanResponse]:
    return ok(actualizar_plan(plan_id, datos, current_user, db), "Plan actualizado correctamente.")
