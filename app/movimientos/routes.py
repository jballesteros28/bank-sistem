from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_user
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken
from schemas.movimiento_schema import (
    MovimientoAjusteAdminCreate,
    MovimientoCashbackCreate,
    MovimientoDepositoCreate,
    MovimientoPagoCreate,
    MovimientoResponse,
    MovimientoRetiroCreate,
    MovimientoReversaCreate,
    MovimientoTransferenciaCreate,
)
from services.movimiento_service import (
    crear_ajuste_admin,
    crear_cashback,
    crear_deposito,
    crear_pago,
    crear_retiro,
    crear_reversa,
    crear_transferencia,
    listar_movimientos,
    obtener_movimiento_por_id,
)
from shared.responses import ApiResponse, ok


router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post("/deposito", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def deposito(
    datos: MovimientoDepositoCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_deposito(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Deposito creado correctamente.")


@router.post("/retiro", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def retiro(
    datos: MovimientoRetiroCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_retiro(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Retiro creado correctamente.")


@router.post("/transferencia", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def transferencia(
    datos: MovimientoTransferenciaCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_transferencia(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Transferencia creada correctamente.")


@router.post("/pago", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def pago(
    datos: MovimientoPagoCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_pago(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Pago creado correctamente.")


@router.post("/cashback", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def cashback(
    datos: MovimientoCashbackCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_cashback(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Cashback creado correctamente.")


@router.post("/ajuste-admin", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_ajuste_admin(datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Ajuste administrativo creado correctamente.")


@router.post("/{movimiento_id}/reversa", response_model=ApiResponse[MovimientoResponse], status_code=status.HTTP_201_CREATED)
def reversa(
    movimiento_id: int,
    datos: MovimientoReversaCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = crear_reversa(movimiento_id, datos, usuario, organizacion.id, db, background_tasks)
    return ok(movimiento, "Reversa creada correctamente.")


@router.get("", response_model=ApiResponse[list[MovimientoResponse]])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[list[MovimientoResponse]]:
    movimientos = listar_movimientos(usuario, organizacion.id, db, skip=skip, limit=limit)
    return ok(movimientos, "Movimientos obtenidos correctamente.")


@router.get("/{movimiento_id}", response_model=ApiResponse[MovimientoResponse])
def obtener(
    movimiento_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> ApiResponse[MovimientoResponse]:
    movimiento = obtener_movimiento_por_id(movimiento_id, usuario, organizacion.id, db)
    return ok(movimiento, "Movimiento obtenido correctamente.")
