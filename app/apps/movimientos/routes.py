from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.schemas import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
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
    crear_retiro,
    crear_reversa,
    crear_transferencia,
    listar_movimientos,
    obtener_movimiento,
)
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post("/deposito", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_deposito(
    datos: MovimientoDepositoCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_deposito(datos, current_user, db), "Deposito creado correctamente.")


@router.post("/retiro", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_retiro(
    datos: MovimientoRetiroCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_retiro(datos, current_user, db), "Retiro creado correctamente.")


@router.post("/transferencia", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_transferencia(
    datos: MovimientoTransferenciaCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_transferencia(datos, current_user, db), "Transferencia creada correctamente.")


@router.post("/pago", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_pago(
    datos: MovimientoPagoCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_pago(datos, current_user, db), "Pago creado correctamente.")


@router.post("/cashback", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_cashback(
    datos: MovimientoCashbackCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_cashback(datos, current_user, db), "Cashback creado correctamente.")


@router.post("/ajuste-admin", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_ajuste_admin(datos, current_user, db), "Ajuste administrativo creado correctamente.")


@router.post("/{movimiento_id}/reversa", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def post_reversa(
    movimiento_id: int,
    datos: MovimientoReversaCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(crear_reversa(movimiento_id, datos, current_user, db), "Reversa creada correctamente.")


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
    movimiento_id: int,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    return ok(obtener_movimiento(movimiento_id, current_user, db), "Movimiento obtenido correctamente.")

