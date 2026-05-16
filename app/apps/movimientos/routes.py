from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.integraciones.webhook_dispatcher import encolar_webhook_evento
from app.apps.notificaciones.services import notificar_movimiento, notificar_pago_organizacion
from app.apps.movimientos.schemas import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
    MovimientoPagoOrganizacionCreate,
    MovimientoPagoCreate,
    MovimientoResponse,
    MovimientoRetiroCreate,
    MovimientoReversaCreate,
    MovimientoTransferenciaCreate,
)
from app.apps.movimientos.services import (
    crear_ajuste_admin,
    crear_cashback,
    crear_deposito,
    crear_pago,
    crear_pago_a_organizacion,
    crear_retiro,
    crear_reversa,
    crear_transferencia,
    listar_movimientos,
    obtener_movimiento,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


def _movimiento_payload(movimiento: MovimientoResponse) -> dict[str, object]:
    return movimiento.model_dump(mode="json", by_alias=True)


@router.post("/deposito", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_deposito(
    datos: MovimientoDepositoCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_deposito(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Deposito creado correctamente.")


@router.post("/retiro", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_retiro(
    datos: MovimientoRetiroCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_retiro(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Retiro creado correctamente.")


@router.post("/transferencia", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_transferencia(
    datos: MovimientoTransferenciaCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_transferencia(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Transferencia creada correctamente.")


@router.post("/pago", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_pago(
    datos: MovimientoPagoCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_pago(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Pago creado correctamente.")


@router.post("/pago-organizacion", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_pago_organizacion(
    datos: MovimientoPagoOrganizacionCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_pago_a_organizacion(datos, current_user, db)
    notificar_pago_organizacion(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    encolar_webhook_evento(
        evento="pago_organizacion.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Pago a organizacion creado correctamente.")


@router.post("/cashback", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_cashback(
    datos: MovimientoCashbackCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_cashback(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Cashback creado correctamente.")


@router.post("/ajuste-admin", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_ajuste_admin(datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.creado",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Ajuste administrativo creado correctamente.")


@router.post("/{movimiento_id}/reversa", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_reversa(
    movimiento_id: UUID,
    datos: MovimientoReversaCreate,
    background_tasks: BackgroundTasks,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_reversa(movimiento_id, datos, current_user, db)
    notificar_movimiento(movimiento, db, background_tasks, actor_usuario_id=current_user.id)
    encolar_webhook_evento(
        evento="movimiento.revertido",
        organizacion_id=movimiento.organizacion_id,
        data=_movimiento_payload(movimiento),
        db=db,
        background_tasks=background_tasks,
    )
    return ok(movimiento, "Reversa creada correctamente.")


@router.get("", response_model=ApiResponse[list[MovimientoResponse]])
def get_movimientos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[MovimientoResponse]]:
    return ok(
        listar_movimientos(current_user, db, skip=skip, limit=limit, organizacion_id=organizacion_id),
        "Movimientos obtenidos correctamente.",
    )


@router.get("/{movimiento_id}", response_model=ApiResponse[MovimientoResponse])
def get_movimiento(
    movimiento_id: UUID,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(obtener_movimiento(movimiento_id, current_user, db), "Movimiento obtenido correctamente.")
