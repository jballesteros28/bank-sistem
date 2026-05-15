from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.apps.movimientos.models import Movimiento
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.planes.services import obtener_o_asignar_plan_organizacion
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.shared.enums import EstadoMovimiento


def validar_limite_usuarios(db: Session, organizacion_id: UUID) -> None:
    plan = _plan_for_organization(db, organizacion_id)
    if plan.limite_usuarios is None:
        return
    total = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.organizacion_id == organizacion_id)) or 0
    _raise_if_limit_reached(total, plan.limite_usuarios, "usuarios", plan.codigo)


def validar_limite_wallets(db: Session, organizacion_id: UUID) -> None:
    plan = _plan_for_organization(db, organizacion_id)
    if plan.limite_wallets is None:
        return
    total = db.scalar(select(func.count()).select_from(Wallet).where(Wallet.organizacion_id == organizacion_id)) or 0
    _raise_if_limit_reached(total, plan.limite_wallets, "wallets", plan.codigo)


def validar_limite_movimientos_mes(db: Session, organizacion_id: UUID) -> None:
    plan = _plan_for_organization(db, organizacion_id)
    if plan.limite_movimientos_mes is None:
        return

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Movimiento)
            .where(
                Movimiento.organizacion_id == organizacion_id,
                Movimiento.estado == EstadoMovimiento.aprobada,
                Movimiento.fecha >= month_start,
            )
        )
        or 0
    )
    _raise_if_limit_reached(total, plan.limite_movimientos_mes, "movimientos mensuales", plan.codigo)


def _plan_for_organization(db: Session, organizacion_id: UUID) -> Plan:
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return obtener_o_asignar_plan_organizacion(db, organizacion)


def _raise_if_limit_reached(current_total: int, limit: int, label: str, plan_code: str) -> None:
    if current_total >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de {label} alcanzado para el plan {plan_code}.",
        )
