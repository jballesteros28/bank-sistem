from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.integraciones.webhook_dispatcher import encolar_webhook_evento
from app.apps.recompensas.schemas import (
    AplicacionRecompensaResponse,
    AplicarRecompensaRequest,
    AplicarRecompensaResponse,
    ReglaRecompensaCreate,
    ReglaRecompensaResponse,
    ReglaRecompensaUpdate,
    SimularRecompensaRequest,
    SimularRecompensaResponse,
)
from app.apps.recompensas.services import (
    actualizar_regla_recompensa,
    aplicar_recompensa,
    crear_regla_recompensa,
    listar_aplicaciones_recompensa,
    listar_mis_aplicaciones_recompensa,
    listar_reglas_recompensa,
    obtener_regla_recompensa,
    simular_recompensa,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/recompensas", tags=["Recompensas"])


def _aplicacion_payload(response: AplicarRecompensaResponse) -> dict[str, object]:
    return response.model_dump(mode="json")


@router.post("/reglas", response_model=ApiResponse[ReglaRecompensaResponse], status_code=status.HTTP_201_CREATED)
def post_regla_recompensa(
    datos: ReglaRecompensaCreate,
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ReglaRecompensaResponse]:
    regla = crear_regla_recompensa(datos, current_user, db, organizacion_id)
    return ok(regla, "Regla de recompensa creada correctamente.")


@router.get("/reglas", response_model=ApiResponse[list[ReglaRecompensaResponse]])
def get_reglas_recompensa(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[ReglaRecompensaResponse]]:
    return ok(
        listar_reglas_recompensa(current_user, db, organizacion_id),
        "Reglas de recompensa obtenidas correctamente.",
    )


@router.get("/reglas/{regla_id}", response_model=ApiResponse[ReglaRecompensaResponse])
def get_regla_recompensa(
    regla_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ReglaRecompensaResponse]:
    return ok(obtener_regla_recompensa(regla_id, current_user, db), "Regla de recompensa obtenida correctamente.")


@router.patch("/reglas/{regla_id}", response_model=ApiResponse[ReglaRecompensaResponse])
def patch_regla_recompensa(
    regla_id: UUID,
    datos: ReglaRecompensaUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ReglaRecompensaResponse]:
    return ok(
        actualizar_regla_recompensa(regla_id, datos, current_user, db),
        "Regla de recompensa actualizada correctamente.",
    )


@router.post("/simular", response_model=ApiResponse[SimularRecompensaResponse])
def post_simular_recompensa(
    datos: SimularRecompensaRequest,
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SimularRecompensaResponse]:
    return ok(simular_recompensa(datos, current_user, db, organizacion_id), "Simulacion calculada correctamente.")


@router.post("/aplicar", response_model=ApiResponse[AplicarRecompensaResponse], status_code=status.HTTP_201_CREATED)
def post_aplicar_recompensa(
    datos: AplicarRecompensaRequest,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[AplicarRecompensaResponse]:
    resultado = aplicar_recompensa(datos, current_user, db)
    encolar_webhook_evento(
        evento="recompensa.aplicada",
        organizacion_id=resultado.aplicacion.organizacion_id,
        data=_aplicacion_payload(resultado),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(resultado, "Recompensa aplicada correctamente.")


@router.get("/aplicaciones/me", response_model=ApiResponse[list[AplicacionRecompensaResponse]])
def get_mis_aplicaciones_recompensa(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[AplicacionRecompensaResponse]]:
    return ok(
        listar_mis_aplicaciones_recompensa(current_user, db, skip, limit),
        "Recompensas del usuario obtenidas correctamente.",
    )


@router.get("/aplicaciones", response_model=ApiResponse[list[AplicacionRecompensaResponse]])
def get_aplicaciones_recompensa(
    organizacion_id: UUID | None = Query(default=None),
    usuario_id: UUID | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[AplicacionRecompensaResponse]]:
    return ok(
        listar_aplicaciones_recompensa(
            current_user,
            db,
            organizacion_id=organizacion_id,
            usuario_id=usuario_id,
            skip=skip,
            limit=limit,
        ),
        "Aplicaciones de recompensa obtenidas correctamente.",
    )
