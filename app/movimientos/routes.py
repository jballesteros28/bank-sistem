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


router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post("/deposito", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def deposito(
    datos: MovimientoDepositoCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_deposito(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/retiro", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def retiro(
    datos: MovimientoRetiroCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_retiro(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/transferencia", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def transferencia(
    datos: MovimientoTransferenciaCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_transferencia(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/pago", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def pago(
    datos: MovimientoPagoCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_pago(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/cashback", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def cashback(
    datos: MovimientoCashbackCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_cashback(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/ajuste-admin", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def ajuste_admin(
    datos: MovimientoAjusteAdminCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_ajuste_admin(datos, usuario, organizacion.id, db, background_tasks)


@router.post("/{movimiento_id}/reversa", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def reversa(
    movimiento_id: int,
    datos: MovimientoReversaCreate,
    background_tasks: BackgroundTasks,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return crear_reversa(movimiento_id, datos, usuario, organizacion.id, db, background_tasks)


@router.get("", response_model=list[MovimientoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> list[MovimientoResponse]:
    return listar_movimientos(usuario, organizacion.id, db, skip=skip, limit=limit)


@router.get("/{movimiento_id}", response_model=MovimientoResponse)
def obtener(
    movimiento_id: int,
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
    db: Session = Depends(get_db),
) -> MovimientoResponse:
    return obtener_movimiento_por_id(movimiento_id, usuario, organizacion.id, db)

