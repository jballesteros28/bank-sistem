from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.integraciones.dependencies import APIKeyContext, require_api_key_scope
from app.apps.integraciones.schemas import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyRevokeResponse,
    WebhookDeliveryResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
)
from app.apps.integraciones.services import (
    actualizar_webhook_endpoint,
    crear_api_key,
    crear_webhook_endpoint,
    desactivar_webhook_endpoint,
    listar_api_keys,
    listar_webhook_deliveries,
    listar_webhook_endpoints,
    registrar_uso_api_key,
    reenviar_webhook_delivery,
    revocar_api_key,
)
from app.apps.integraciones.webhook_dispatcher import encolar_webhook_evento
from app.apps.movimientos.models import Movimiento
from app.apps.movimientos.schemas import MovimientoCashbackCreate, MovimientoDepositoCreate, MovimientoResponse
from app.apps.movimientos.services import crear_cashback_api_key, crear_deposito_api_key
from app.apps.wallets.models import Wallet
from app.apps.wallets.schemas import WalletResponse
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/integraciones", tags=["Integraciones"])
ext_router = APIRouter(prefix="/ext", tags=["Integraciones externas"])


@router.post("/api-keys", response_model=ApiResponse[APIKeyCreateResponse], status_code=status.HTTP_201_CREATED)
def post_api_key(
    datos: APIKeyCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[APIKeyCreateResponse]:
    return ok(crear_api_key(datos, current_user, db), "API Key creada correctamente.")


@router.get("/api-keys", response_model=ApiResponse[list[APIKeyResponse]])
def get_api_keys(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[APIKeyResponse]]:
    return ok(listar_api_keys(current_user, db, organizacion_id), "API Keys obtenidas correctamente.")


@router.delete("/api-keys/{api_key_id}", response_model=ApiResponse[APIKeyRevokeResponse])
def delete_api_key(
    api_key_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[APIKeyRevokeResponse]:
    return ok(revocar_api_key(api_key_id, current_user, db), "API Key revocada correctamente.")


@router.post("/webhooks", response_model=ApiResponse[WebhookEndpointResponse], status_code=status.HTTP_201_CREATED)
def post_webhook(
    datos: WebhookEndpointCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WebhookEndpointResponse]:
    return ok(crear_webhook_endpoint(datos, current_user, db), "Webhook creado correctamente.")


@router.get("/webhooks", response_model=ApiResponse[list[WebhookEndpointResponse]])
def get_webhooks(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[WebhookEndpointResponse]]:
    return ok(listar_webhook_endpoints(current_user, db, organizacion_id), "Webhooks obtenidos correctamente.")


@router.patch("/webhooks/{webhook_id}", response_model=ApiResponse[WebhookEndpointResponse])
def patch_webhook(
    webhook_id: UUID,
    datos: WebhookEndpointUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WebhookEndpointResponse]:
    return ok(actualizar_webhook_endpoint(webhook_id, datos, current_user, db), "Webhook actualizado correctamente.")


@router.delete("/webhooks/{webhook_id}", response_model=ApiResponse[WebhookEndpointResponse])
def delete_webhook(
    webhook_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WebhookEndpointResponse]:
    return ok(desactivar_webhook_endpoint(webhook_id, current_user, db), "Webhook desactivado correctamente.")


@router.get("/webhooks/deliveries", response_model=ApiResponse[list[WebhookDeliveryResponse]])
def get_webhook_deliveries(
    organizacion_id: UUID | None = Query(default=None),
    webhook_endpoint_id: UUID | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[WebhookDeliveryResponse]]:
    deliveries = listar_webhook_deliveries(
        current_user,
        db,
        organizacion_id=organizacion_id,
        webhook_endpoint_id=webhook_endpoint_id,
        skip=skip,
        limit=limit,
    )
    return ok(deliveries, "Deliveries obtenidos correctamente.")


@router.post("/webhooks/deliveries/{delivery_id}/reenviar", response_model=ApiResponse[WebhookDeliveryResponse])
def post_reenviar_webhook_delivery(
    delivery_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WebhookDeliveryResponse]:
    delivery = reenviar_webhook_delivery(delivery_id, current_user, db, background_tasks)
    return ok(delivery, "Reenvio de webhook agendado correctamente.")


def _movement_payload(movimiento: MovimientoResponse) -> dict[str, object]:
    return movimiento.model_dump(mode="json", by_alias=True)


@ext_router.get("/wallets/{wallet_id}", response_model=ApiResponse[WalletResponse])
def ext_get_wallet(
    wallet_id: UUID,
    context: APIKeyContext = Depends(require_api_key_scope("wallets:read")),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletResponse]:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None or wallet.organizacion_id != context.organizacion.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet no encontrada.")
    registrar_uso_api_key(context.api_key, db, endpoint="GET /api/v1/ext/wallets/{wallet_id}", scope="wallets:read")
    return ok(WalletResponse.model_validate(wallet), "Wallet obtenida correctamente.")


@ext_router.post("/movimientos/cashback", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def ext_post_cashback(
    datos: MovimientoCashbackCreate,
    background_tasks: BackgroundTasks,
    context: APIKeyContext = Depends(require_api_key_scope("movimientos:write")),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_cashback_api_key(
        datos,
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        db=db,
    )
    registrar_uso_api_key(
        context.api_key,
        db,
        endpoint="POST /api/v1/ext/movimientos/cashback",
        scope="movimientos:write",
    )
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=context.organizacion.id,
        data=_movement_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Cashback creado correctamente.")


@ext_router.post("/movimientos/deposito", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def ext_post_deposito(
    datos: MovimientoDepositoCreate,
    background_tasks: BackgroundTasks,
    context: APIKeyContext = Depends(require_api_key_scope("movimientos:write")),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_deposito_api_key(
        datos,
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        db=db,
    )
    registrar_uso_api_key(
        context.api_key,
        db,
        endpoint="POST /api/v1/ext/movimientos/deposito",
        scope="movimientos:write",
    )
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=context.organizacion.id,
        data=_movement_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Deposito creado correctamente.")


@ext_router.get("/movimientos", response_model=ApiResponse[list[MovimientoResponse]])
def ext_get_movimientos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: APIKeyContext = Depends(require_api_key_scope("movimientos:read")),
    db: Session = Depends(get_db),
) -> ApiResponse[list[MovimientoResponse]]:
    movimientos = db.scalars(
        select(Movimiento)
        .where(Movimiento.organizacion_id == context.organizacion.id)
        .order_by(Movimiento.fecha.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    registrar_uso_api_key(context.api_key, db, endpoint="GET /api/v1/ext/movimientos", scope="movimientos:read")
    return ok(
        [MovimientoResponse.model_validate(movimiento) for movimiento in movimientos],
        "Movimientos obtenidos correctamente.",
    )
