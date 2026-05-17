from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.apps.auditoria.services import registrar_evento_usuario
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.models import Movimiento
from app.apps.movimientos.schemas import MovimientoResponse
from app.apps.notificaciones.services import crear_notificacion_interna
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.limit_service import validar_limite_movimientos_mes
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.recompensas.permissions import (
    ensure_can_apply_rewards,
    ensure_can_manage_rewards,
    ensure_can_read_rewards,
)
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
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.core.permissions import is_super_admin
from app.shared.enums import (
    EstadoMovimiento,
    EstadoReglaRecompensa,
    EstadoWallet,
    MonedaRecompensa,
    MonedaWallet,
    OwnerTypeWallet,
    TipoMovimiento,
    TipoNotificacion,
    TipoRecompensa,
)
from app.shared.utils import normalize_decimal


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _amount(value: Decimal | str | int | float) -> Decimal:
    return normalize_decimal(value)


def _json_metadata(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, (UUID, Decimal)):
            cleaned[key] = str(item)
        elif isinstance(item, datetime):
            cleaned[key] = item.isoformat()
        else:
            cleaned[key] = item
    return cleaned


def _reward_currency_to_wallet_currency(moneda: MonedaRecompensa) -> MonedaWallet:
    return MonedaWallet(moneda.value)


def _resolve_organization_for_write(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> UUID:
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar una organizacion.")
    if db.get(Organizacion, scope_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return scope_id


def _rules_scope_query(current_user: DatosUsuarioToken, organizacion_id: UUID | None = None):
    query = select(ReglaRecompensa)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(ReglaRecompensa.organizacion_id == organizacion_id)
    else:
        scope_id = resolve_organization_scope(current_user, organizacion_id)
        query = query.where(ReglaRecompensa.organizacion_id == scope_id)
    return query


def _get_rule_scoped(
    regla_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> ReglaRecompensa:
    regla = db.get(ReglaRecompensa, regla_id)
    if regla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla de recompensa no encontrada.")
    if not is_super_admin(current_user.rol) and regla.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla de recompensa no encontrada.")
    return regla


def _validate_rule_model(regla: ReglaRecompensa) -> None:
    if regla.porcentaje_cashback is None and regla.monto_fijo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe informar porcentaje_cashback o monto_fijo.",
        )
    if regla.porcentaje_cashback is not None:
        porcentaje = _amount(regla.porcentaje_cashback)
        if porcentaje <= Decimal("0.00") or porcentaje > Decimal("100.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El porcentaje debe ser mayor a 0 y menor o igual a 100.",
            )
    for field_name in ("monto_fijo", "monto_maximo_recompensa"):
        value = getattr(regla, field_name)
        if value is not None and _amount(value) <= Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} debe ser mayor a 0.")
    if regla.monto_minimo_compra is not None and _amount(regla.monto_minimo_compra) < Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="monto_minimo_compra debe ser mayor o igual a 0.",
        )
    fecha_inicio = _as_utc(regla.fecha_inicio)
    fecha_fin = _as_utc(regla.fecha_fin)
    if fecha_inicio is not None and fecha_fin is not None and fecha_fin <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin debe ser posterior a fecha_inicio.",
        )


def crear_regla_recompensa(
    datos: ReglaRecompensaCreate,
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> ReglaRecompensaResponse:
    ensure_can_manage_rewards(current_user)
    scope_id = _resolve_organization_for_write(current_user, db, organizacion_id)
    regla = ReglaRecompensa(
        organizacion_id=scope_id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        tipo=datos.tipo,
        estado=EstadoReglaRecompensa.activa,
        porcentaje_cashback=datos.porcentaje_cashback,
        monto_fijo=datos.monto_fijo,
        moneda_recompensa=datos.moneda_recompensa,
        monto_minimo_compra=datos.monto_minimo_compra,
        monto_maximo_recompensa=datos.monto_maximo_recompensa,
        acumulable=datos.acumulable,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
    )
    _validate_rule_model(regla)
    db.add(regla)
    db.commit()
    db.refresh(regla)
    _audit_rule_change(
        db,
        current_user=current_user,
        regla=regla,
        evento="regla_recompensa_creada",
        mensaje="Regla de recompensa creada.",
    )
    return ReglaRecompensaResponse.model_validate(regla)


def listar_reglas_recompensa(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[ReglaRecompensaResponse]:
    ensure_can_read_rewards(current_user)
    query = _rules_scope_query(current_user, organizacion_id).order_by(
        ReglaRecompensa.fecha_creacion.desc(),
        ReglaRecompensa.id.asc(),
    )
    return [ReglaRecompensaResponse.model_validate(regla) for regla in db.scalars(query).all()]


def obtener_regla_recompensa(
    regla_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> ReglaRecompensaResponse:
    ensure_can_read_rewards(current_user)
    return ReglaRecompensaResponse.model_validate(_get_rule_scoped(regla_id, current_user, db))


def actualizar_regla_recompensa(
    regla_id: UUID,
    datos: ReglaRecompensaUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> ReglaRecompensaResponse:
    ensure_can_manage_rewards(current_user)
    regla = _get_rule_scoped(regla_id, current_user, db)
    cambios = datos.model_dump(exclude_unset=True)
    for field, value in cambios.items():
        setattr(regla, field, value)
    _validate_rule_model(regla)
    db.add(regla)
    db.commit()
    db.refresh(regla)
    _audit_rule_change(
        db,
        current_user=current_user,
        regla=regla,
        evento="regla_recompensa_actualizada",
        mensaje="Regla de recompensa actualizada.",
    )
    return ReglaRecompensaResponse.model_validate(regla)


def activar_regla_recompensa(
    regla_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> ReglaRecompensaResponse:
    return actualizar_regla_recompensa(
        regla_id,
        ReglaRecompensaUpdate(estado=EstadoReglaRecompensa.activa),
        current_user,
        db,
    )


def pausar_regla_recompensa(
    regla_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> ReglaRecompensaResponse:
    return actualizar_regla_recompensa(
        regla_id,
        ReglaRecompensaUpdate(estado=EstadoReglaRecompensa.pausada),
        current_user,
        db,
    )


def _calculate_reward(regla: ReglaRecompensa, monto_compra: Decimal) -> Decimal:
    if regla.porcentaje_cashback is not None:
        reward = monto_compra * _amount(regla.porcentaje_cashback) / Decimal("100.00")
    elif regla.monto_fijo is not None:
        reward = _amount(regla.monto_fijo)
    else:
        reward = Decimal("0.00")
    reward = _amount(reward)
    if regla.monto_maximo_recompensa is not None:
        reward = min(reward, _amount(regla.monto_maximo_recompensa))
    return _amount(reward)


def _evaluate_rule(
    regla: ReglaRecompensa,
    monto_compra: Decimal,
    *,
    now: datetime,
) -> SimularRecompensaResponse:
    if regla.estado != EstadoReglaRecompensa.activa:
        return SimularRecompensaResponse(
            aplica=False,
            regla_id=regla.id,
            nombre_regla=regla.nombre,
            monto_compra=monto_compra,
            monto_recompensa=Decimal("0.00"),
            moneda_recompensa=regla.moneda_recompensa,
            motivo="La regla no esta activa.",
        )
    if regla.monto_minimo_compra is not None and monto_compra < _amount(regla.monto_minimo_compra):
        return SimularRecompensaResponse(
            aplica=False,
            regla_id=regla.id,
            nombre_regla=regla.nombre,
            monto_compra=monto_compra,
            monto_recompensa=Decimal("0.00"),
            moneda_recompensa=regla.moneda_recompensa,
            motivo="El monto de compra no alcanza el minimo de la regla.",
        )
    fecha_inicio = _as_utc(regla.fecha_inicio)
    fecha_fin = _as_utc(regla.fecha_fin)
    if fecha_inicio is not None and now < fecha_inicio:
        return SimularRecompensaResponse(
            aplica=False,
            regla_id=regla.id,
            nombre_regla=regla.nombre,
            monto_compra=monto_compra,
            monto_recompensa=Decimal("0.00"),
            moneda_recompensa=regla.moneda_recompensa,
            motivo="La regla todavia no esta vigente.",
        )
    if fecha_fin is not None and now > fecha_fin:
        return SimularRecompensaResponse(
            aplica=False,
            regla_id=regla.id,
            nombre_regla=regla.nombre,
            monto_compra=monto_compra,
            monto_recompensa=Decimal("0.00"),
            moneda_recompensa=regla.moneda_recompensa,
            motivo="La regla ya no esta vigente.",
        )
    reward = _calculate_reward(regla, monto_compra)
    if reward <= Decimal("0.00"):
        return SimularRecompensaResponse(
            aplica=False,
            regla_id=regla.id,
            nombre_regla=regla.nombre,
            monto_compra=monto_compra,
            monto_recompensa=Decimal("0.00"),
            moneda_recompensa=regla.moneda_recompensa,
            motivo="La regla no genera recompensa.",
        )
    return SimularRecompensaResponse(
        aplica=True,
        regla_id=regla.id,
        nombre_regla=regla.nombre,
        monto_compra=monto_compra,
        monto_recompensa=reward,
        moneda_recompensa=regla.moneda_recompensa,
        motivo="Regla aplicable.",
    )


def _find_applicable_rule(
    datos: SimularRecompensaRequest,
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> SimularRecompensaResponse:
    now = _now()
    monto_compra = _amount(datos.monto_compra)
    if datos.regla_id is not None:
        regla = _get_rule_scoped(datos.regla_id, current_user, db)
        return _evaluate_rule(regla, monto_compra, now=now)

    scope_id = resolve_organization_scope(current_user, organizacion_id)
    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar una organizacion.")
    query = select(ReglaRecompensa).where(ReglaRecompensa.organizacion_id == scope_id)
    if datos.tipo is not None:
        query = query.where(ReglaRecompensa.tipo == datos.tipo)
    reglas = db.scalars(
        query.order_by(ReglaRecompensa.fecha_creacion.asc(), ReglaRecompensa.id.asc())
    ).all()
    for regla in reglas:
        result = _evaluate_rule(regla, monto_compra, now=now)
        if result.aplica:
            return result
    return SimularRecompensaResponse(
        aplica=False,
        regla_id=None,
        nombre_regla=None,
        monto_compra=monto_compra,
        monto_recompensa=Decimal("0.00"),
        moneda_recompensa=None,
        motivo="No hay reglas aplicables.",
    )


def simular_recompensa(
    datos: SimularRecompensaRequest,
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> SimularRecompensaResponse:
    ensure_can_read_rewards(current_user)
    return _find_applicable_rule(datos, current_user, db, organizacion_id)


def _get_user_or_404(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return usuario


def _get_wallet_locked(db: Session, wallet_id: UUID) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.id == wallet_id).with_for_update())
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet destino no encontrada.")
    return wallet


def _resolve_apply_organization(
    current_user: DatosUsuarioToken,
    usuario: Usuario,
    wallet: Wallet,
) -> UUID:
    if usuario.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario sin organizacion.")
    if wallet.organizacion_id != usuario.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    if not is_super_admin(current_user.rol) and usuario.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    return usuario.organizacion_id


def _ensure_reward_wallet(wallet: Wallet, usuario_id: UUID, moneda_recompensa: MonedaRecompensa) -> None:
    if wallet.owner_type != OwnerTypeWallet.usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet destino debe ser de usuario.")
    if wallet.usuario_id != usuario_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La wallet destino no pertenece al usuario.")
    if wallet.estado != EstadoWallet.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La wallet destino no esta activa.")
    if wallet.moneda != _reward_currency_to_wallet_currency(moneda_recompensa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La moneda de la wallet destino no coincide con la recompensa.",
        )


def _movement_type_for_reward(tipo: TipoRecompensa) -> TipoMovimiento:
    if tipo == TipoRecompensa.cashback:
        return TipoMovimiento.cashback
    return TipoMovimiento.credito_tienda


def _duplicate_reference_exists(db: Session, organizacion_id: UUID, referencia_externa: str | None) -> bool:
    if not referencia_externa:
        return False
    existing = db.scalar(
        select(AplicacionRecompensa.id).where(
            AplicacionRecompensa.organizacion_id == organizacion_id,
            AplicacionRecompensa.referencia_externa == referencia_externa,
        )
    )
    return existing is not None


def aplicar_recompensa(
    datos: AplicarRecompensaRequest,
    current_user: DatosUsuarioToken,
    db: Session,
) -> AplicarRecompensaResponse:
    ensure_can_apply_rewards(current_user)
    usuario = _get_user_or_404(db, datos.usuario_id)
    wallet = _get_wallet_locked(db, datos.wallet_destino_id)
    organization_id = _resolve_apply_organization(current_user, usuario, wallet)
    if _duplicate_reference_exists(db, organization_id, datos.referencia_externa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una recompensa aplicada con esa referencia externa.",
        )

    simulation = _find_applicable_rule(
        SimularRecompensaRequest(
            monto_compra=datos.monto_compra,
            regla_id=datos.regla_id,
            metadata=datos.metadata,
        ),
        current_user,
        db,
        organization_id,
    )
    if not simulation.aplica or simulation.regla_id is None or simulation.moneda_recompensa is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=simulation.motivo)

    regla = db.get(ReglaRecompensa, simulation.regla_id)
    if regla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla de recompensa no encontrada.")
    if regla.organizacion_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede operar entre organizaciones.")
    _ensure_reward_wallet(wallet, usuario.id, regla.moneda_recompensa)

    monto_compra = _amount(datos.monto_compra)
    monto_recompensa = _amount(simulation.monto_recompensa)
    validar_limite_movimientos_mes(db, organization_id)
    wallet.saldo = _amount(wallet.saldo) + monto_recompensa
    metadata_movimiento = _json_metadata(
        {
            **(datos.metadata or {}),
            "regla_id": regla.id,
            "tipo_recompensa": regla.tipo.value,
            "moneda_recompensa": regla.moneda_recompensa.value,
            "monto_compra": str(monto_compra),
        }
    )
    movimiento = Movimiento(
        wallet_origen_id=None,
        wallet_destino_id=wallet.id,
        organizacion_id=organization_id,
        monto=monto_recompensa,
        moneda=_reward_currency_to_wallet_currency(regla.moneda_recompensa),
        tipo=_movement_type_for_reward(regla.tipo),
        estado=EstadoMovimiento.aprobada,
        descripcion=f"Recompensa aplicada: {regla.nombre}",
        referencia_externa=datos.referencia_externa,
        metadata_movimiento=metadata_movimiento,
        es_reversa=False,
    )
    db.add_all([wallet, movimiento])
    try:
        db.flush()
        aplicacion = AplicacionRecompensa(
            organizacion_id=organization_id,
            regla_id=regla.id,
            usuario_id=usuario.id,
            wallet_destino_id=wallet.id,
            movimiento_id=movimiento.id,
            monto_compra=monto_compra,
            monto_recompensa=monto_recompensa,
            moneda_recompensa=regla.moneda_recompensa,
            referencia_externa=datos.referencia_externa,
            metadata_aplicacion=_json_metadata(datos.metadata),
        )
        db.add(aplicacion)
        db.commit()
        db.refresh(aplicacion)
        db.refresh(movimiento)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una recompensa aplicada con esa referencia externa.",
        )
    except Exception:
        db.rollback()
        raise

    aplicacion_response = AplicacionRecompensaResponse.model_validate(aplicacion)
    movimiento_response = MovimientoResponse.model_validate(movimiento)
    _notify_reward_applied(
        db,
        aplicacion=aplicacion_response,
        movimiento=movimiento_response,
        usuario=usuario,
        regla=regla,
        actor_usuario_id=current_user.id,
    )
    _audit_reward_applied(
        db,
        current_user=current_user,
        aplicacion=aplicacion_response,
        movimiento=movimiento_response,
        regla=regla,
    )
    return AplicarRecompensaResponse(aplicacion=aplicacion_response, movimiento=movimiento_response)


def listar_aplicaciones_recompensa(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    usuario_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AplicacionRecompensaResponse]:
    ensure_can_read_rewards(current_user)
    query = select(AplicacionRecompensa)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(AplicacionRecompensa.organizacion_id == organizacion_id)
    else:
        scope_id = resolve_organization_scope(current_user, organizacion_id)
        query = query.where(AplicacionRecompensa.organizacion_id == scope_id)
    if usuario_id is not None:
        query = query.where(AplicacionRecompensa.usuario_id == usuario_id)
    aplicaciones = db.scalars(
        query.order_by(AplicacionRecompensa.fecha_creacion.desc()).offset(skip).limit(limit)
    ).all()
    return [AplicacionRecompensaResponse.model_validate(aplicacion) for aplicacion in aplicaciones]


def listar_mis_aplicaciones_recompensa(
    current_user: DatosUsuarioToken,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[AplicacionRecompensaResponse]:
    if current_user.organizacion_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin organizacion.")
    query = (
        select(AplicacionRecompensa)
        .where(
            AplicacionRecompensa.organizacion_id == current_user.organizacion_id,
            AplicacionRecompensa.usuario_id == current_user.id,
        )
        .order_by(AplicacionRecompensa.fecha_creacion.desc())
        .offset(skip)
        .limit(limit)
    )
    return [AplicacionRecompensaResponse.model_validate(aplicacion) for aplicacion in db.scalars(query).all()]


def _audit_rule_change(
    db: Session,
    *,
    current_user: DatosUsuarioToken,
    regla: ReglaRecompensa,
    evento: str,
    mensaje: str,
) -> None:
    try:
        registrar_evento_usuario(
            db,
            organizacion_id=regla.organizacion_id,
            actor_usuario_id=current_user.id,
            evento=evento,
            mensaje=mensaje,
            metadata={"regla_id": str(regla.id), "tipo": regla.tipo.value, "estado": regla.estado.value},
        )
    except Exception:
        db.rollback()


def _notify_reward_applied(
    db: Session,
    *,
    aplicacion: AplicacionRecompensaResponse,
    movimiento: MovimientoResponse,
    usuario: Usuario,
    regla: ReglaRecompensa,
    actor_usuario_id: UUID | None = None,
) -> None:
    try:
        crear_notificacion_interna(
            organizacion_id=aplicacion.organizacion_id,
            usuario_id=usuario.id,
            tipo=TipoNotificacion.recompensa_aplicada,
            titulo="Recompensa acreditada",
            mensaje=f"Recibiste {aplicacion.monto_recompensa} {aplicacion.moneda_recompensa.value} en tu wallet.",
            db=db,
            metadata={
                "aplicacion_id": aplicacion.id,
                "movimiento_id": movimiento.id,
                "regla_id": regla.id,
                "tipo_recompensa": regla.tipo.value,
                "monto_compra": str(aplicacion.monto_compra),
                "monto_recompensa": str(aplicacion.monto_recompensa),
                "moneda_recompensa": aplicacion.moneda_recompensa.value,
            },
            actor_usuario_id=actor_usuario_id,
        )
    except Exception:
        db.rollback()


def _audit_reward_applied(
    db: Session,
    *,
    current_user: DatosUsuarioToken,
    aplicacion: AplicacionRecompensaResponse,
    movimiento: MovimientoResponse,
    regla: ReglaRecompensa,
) -> None:
    try:
        registrar_evento_usuario(
            db,
            organizacion_id=aplicacion.organizacion_id,
            actor_usuario_id=current_user.id,
            evento="recompensa_aplicada",
            mensaje="Recompensa aplicada.",
            metadata={
                "aplicacion_id": str(aplicacion.id),
                "movimiento_id": str(movimiento.id),
                "regla_id": str(regla.id),
                "tipo_recompensa": regla.tipo.value,
                "monto_compra": str(aplicacion.monto_compra),
                "monto_recompensa": str(aplicacion.monto_recompensa),
                "moneda_recompensa": aplicacion.moneda_recompensa.value,
                "wallet_destino_id": str(aplicacion.wallet_destino_id),
                "usuario_id": str(aplicacion.usuario_id),
            },
        )
    except Exception:
        db.rollback()
