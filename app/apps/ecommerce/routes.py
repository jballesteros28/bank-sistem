from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.ecommerce.schemas import EcommerceOrderEventResponse, EcommerceOrderPaidRequest, EcommerceOrderPaidResponse
from app.apps.ecommerce.services import listar_order_events, obtener_order_event, registrar_order_paid
from app.apps.integraciones.dependencies import APIKeyContext, require_api_key_scope
from app.apps.integraciones.services import registrar_uso_api_key
from app.apps.integraciones.webhook_dispatcher import encolar_webhook_evento
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/ecommerce", tags=["Ecommerce"])
ext_router = APIRouter(prefix="/ext/ecommerce", tags=["Ecommerce externo"])


def _order_payload(response: EcommerceOrderPaidResponse) -> dict[str, object]:
    return response.model_dump(mode="json")


@ext_router.post(
    "/order-paid",
    response_model=ApiResponse[EcommerceOrderPaidResponse],
    status_code=status.HTTP_201_CREATED,
)
def ext_post_order_paid(
    datos: EcommerceOrderPaidRequest,
    background_tasks: BackgroundTasks,
    context: APIKeyContext = Depends(require_api_key_scope("ecommerce:write")),
    db: Session = Depends(get_db),
) -> ApiResponse[EcommerceOrderPaidResponse]:
    result = registrar_order_paid(datos, context, db)
    registrar_uso_api_key(
        context.api_key,
        db,
        endpoint="POST /api/v1/ext/ecommerce/order-paid",
        scope="ecommerce:write",
    )
    payload = _order_payload(result)
    encolar_webhook_evento(
        evento="ecommerce.order_paid",
        organizacion_id=context.organizacion.id,
        data=payload,
        db=db,
        background_tasks=background_tasks,
    )
    if result.recompensa_aplicada is not None:
        encolar_webhook_evento(
            evento="ecommerce.order_processed",
            organizacion_id=context.organizacion.id,
            data=payload,
            db=db,
            background_tasks=background_tasks,
        )
        encolar_webhook_evento(
            evento="recompensa.aplicada",
            organizacion_id=context.organizacion.id,
            data={
                "aplicacion": result.recompensa_aplicada.model_dump(mode="json"),
                "movimiento": result.movimiento.model_dump(mode="json") if result.movimiento else None,
                "ecommerce_event": result.event.model_dump(mode="json"),
            },
            db=db,
            background_tasks=background_tasks,
        )
    elif result.event.error_procesamiento:
        encolar_webhook_evento(
            evento="ecommerce.order_failed",
            organizacion_id=context.organizacion.id,
            data=payload,
            db=db,
            background_tasks=background_tasks,
        )
    return ok(result, result.mensaje)


@router.get("/orders", response_model=ApiResponse[list[EcommerceOrderEventResponse]])
def get_ecommerce_orders(
    organizacion_id: UUID | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[EcommerceOrderEventResponse]]:
    return ok(
        listar_order_events(current_user, db, organizacion_id=organizacion_id, skip=skip, limit=limit),
        "Eventos ecommerce obtenidos correctamente.",
    )


@router.get("/orders/{event_id}", response_model=ApiResponse[EcommerceOrderEventResponse])
def get_ecommerce_order(
    event_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[EcommerceOrderEventResponse]:
    return ok(obtener_order_event(event_id, current_user, db), "Evento ecommerce obtenido correctamente.")
