from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.planes.permissions import ensure_can_manage_plans, ensure_can_view_current_plan
from app.apps.planes.schemas import (
    CambiarPlanOrganizacionResponse,
    PlanActualResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
)
from app.core.permissions import is_super_admin


BASE_PLANS: tuple[dict[str, object], ...] = (
    {
        "nombre": "Free",
        "codigo": "free",
        "precio_mensual": Decimal("0.00"),
        "limite_usuarios": 10,
        "limite_wallets": 3,
        "limite_movimientos_mes": 100,
        "permite_webhooks": False,
        "permite_white_label": False,
    },
    {
        "nombre": "Starter",
        "codigo": "starter",
        "precio_mensual": Decimal("19.00"),
        "limite_usuarios": 100,
        "limite_wallets": 50,
        "limite_movimientos_mes": 2000,
        "permite_webhooks": False,
        "permite_white_label": False,
    },
    {
        "nombre": "Pro",
        "codigo": "pro",
        "precio_mensual": Decimal("49.00"),
        "limite_usuarios": 1000,
        "limite_wallets": None,
        "limite_movimientos_mes": 50000,
        "permite_webhooks": True,
        "permite_white_label": True,
    },
    {
        "nombre": "Enterprise",
        "codigo": "enterprise",
        "precio_mensual": Decimal("199.00"),
        "limite_usuarios": None,
        "limite_wallets": None,
        "limite_movimientos_mes": None,
        "permite_webhooks": True,
        "permite_white_label": True,
    },
)


def asegurar_planes_base(db: Session, *, commit: bool = True) -> list[Plan]:
    existing_codes = set(db.scalars(select(Plan.codigo)).all())
    created: list[Plan] = []
    for plan_data in BASE_PLANS:
        if str(plan_data["codigo"]) in existing_codes:
            continue
        plan = Plan(**plan_data)
        db.add(plan)
        created.append(plan)

    if created and commit:
        db.commit()
        for plan in created:
            db.refresh(plan)
    elif created:
        db.flush()

    return db.scalars(select(Plan).order_by(Plan.precio_mensual.asc(), Plan.codigo.asc())).all()


def crear_plan(datos: PlanCreate, current_user: DatosUsuarioToken, db: Session) -> PlanResponse:
    ensure_can_manage_plans(current_user)
    _ensure_unique_plan_fields(db, datos.nombre, datos.codigo)
    plan = Plan(**datos.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return PlanResponse.model_validate(plan)


def listar_planes(current_user: DatosUsuarioToken, db: Session) -> list[PlanResponse]:
    asegurar_planes_base(db)
    query = select(Plan).order_by(Plan.precio_mensual.asc(), Plan.codigo.asc())
    if not is_super_admin(current_user.rol):
        query = query.where(Plan.activo.is_(True))
    return [PlanResponse.model_validate(plan) for plan in db.scalars(query).all()]


def obtener_plan_por_id(plan_id: UUID, current_user: DatosUsuarioToken, db: Session) -> PlanResponse:
    plan = _get_plan_or_404(db, plan_id)
    if not plan.activo and not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado.")
    return PlanResponse.model_validate(plan)


def obtener_plan_por_codigo(codigo: str, db: Session) -> Plan | None:
    return db.scalar(select(Plan).where(Plan.codigo == codigo))


def actualizar_plan(
    plan_id: UUID,
    datos: PlanUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> PlanResponse:
    ensure_can_manage_plans(current_user)
    plan = _get_plan_or_404(db, plan_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios or "codigo" in cambios:
        _ensure_unique_plan_fields(
            db,
            cambios.get("nombre", plan.nombre),
            cambios.get("codigo", plan.codigo),
            plan_id=plan.id,
        )
    for field, value in cambios.items():
        setattr(plan, field, value)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return PlanResponse.model_validate(plan)


def cambiar_plan_organizacion(
    organizacion_id: UUID,
    plan_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> CambiarPlanOrganizacionResponse:
    ensure_can_manage_plans(current_user)
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    plan = _get_plan_or_404(db, plan_id)
    if not plan.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede asignar un plan inactivo.")

    organizacion.plan_id = plan.id
    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    db.refresh(plan)
    return CambiarPlanOrganizacionResponse(
        organizacion_id=organizacion.id,
        plan=PlanResponse.model_validate(plan),
        mensaje="Plan de organizacion actualizado.",
    )


def obtener_plan_actual_de_organizacion(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> PlanActualResponse:
    ensure_can_view_current_plan(current_user)
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar una organizacion.")
    organizacion = db.get(Organizacion, scope_id)
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    plan = obtener_o_asignar_plan_organizacion(db, organizacion, commit=True)
    return PlanActualResponse(organizacion_id=organizacion.id, plan=PlanResponse.model_validate(plan))


def obtener_o_asignar_plan_organizacion(db: Session, organizacion: Organizacion, *, commit: bool = False) -> Plan:
    if organizacion.plan_id is not None:
        plan = db.get(Plan, organizacion.plan_id)
        if plan is not None:
            return plan

    free_plan = obtener_plan_por_codigo("free", db)
    if free_plan is None:
        asegurar_planes_base(db, commit=commit)
        free_plan = obtener_plan_por_codigo("free", db)
    if free_plan is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Plan free no disponible.")

    organizacion.plan_id = free_plan.id
    db.add(organizacion)
    if commit:
        db.commit()
        db.refresh(organizacion)
    else:
        db.flush()
    return free_plan


def _get_plan_or_404(db: Session, plan_id: UUID) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado.")
    return plan


def _ensure_unique_plan_fields(db: Session, nombre: str, codigo: str, plan_id: UUID | None = None) -> None:
    query = select(Plan).where((Plan.nombre == nombre) | (Plan.codigo == codigo))
    if plan_id is not None:
        query = query.where(Plan.id != plan_id)
    existing = db.scalar(query)
    if existing is None:
        return
    if existing.nombre == nombre:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un plan con ese nombre.")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un plan con ese codigo.")
