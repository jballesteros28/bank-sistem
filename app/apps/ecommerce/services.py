from __future__ import annotations

import secrets
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.apps.auditoria.services import registrar_evento_api_key
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.ecommerce.models import EcommerceOrderEvent
from app.apps.ecommerce.permissions import ensure_can_read_ecommerce
from app.apps.ecommerce.schemas import (
    EcommerceOrderEventResponse,
    EcommerceOrderPaidRequest,
    EcommerceOrderPaidResponse,
)
from app.apps.integraciones.dependencies import APIKeyContext
from app.apps.movimientos.models import Movimiento
from app.apps.movimientos.schemas import MovimientoResponse
from app.apps.notificaciones.services import crear_notificacion_interna
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.limit_service import validar_limite_movimientos_mes, validar_limite_usuarios, validar_limite_wallets
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.recompensas.schemas import AplicacionRecompensaResponse
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.core.permissions import is_super_admin
from app.core.security import hash_password
from app.shared.enums import (
    EstadoMovimiento,
    EstadoOrganizacion,
    EstadoReglaRecompensa,
    EstadoWallet,
    MonedaRecompensa,
    MonedaWallet,
    OwnerTypeWallet,
    RolUsuario,
    TipoMovimiento,
    TipoNotificacion,
    TipoRecompensa,
    TipoWallet,
)
from app.shared.utils import normalize_decimal, normalize_email


NO_REWARD_RULE_MESSAGE = "No hay regla de recompensa aplicable"


class EcommerceProcessingError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


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


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _json_metadata(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return _jsonable(value)


def _audit_api_key(
    db: Session,
    *,
    evento: str,
    mensaje: str,
    organizacion_id: UUID,
    actor_api_key_id: UUID,
    metadata: dict[str, Any] | None = None,
    nivel: str = "INFO",
) -> None:
    try:
        registrar_evento_api_key(
            db,
            organizacion_id=organizacion_id,
            actor_api_key_id=actor_api_key_id,
            evento=evento,
            mensaje=mensaje,
            nivel=nivel,
            metadata=_json_metadata(metadata),
        )
    except Exception:
        db.rollback()


def _validate_supported_currency(currency: str) -> MonedaWallet:
    try:
        return MonedaWallet(currency)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Moneda no soportada para ecommerce: {currency}.",
        )


def _reward_currency_to_wallet_currency(moneda: MonedaRecompensa) -> MonedaWallet:
    return MonedaWallet(moneda.value)


def _movement_type_for_reward(tipo: TipoRecompensa) -> TipoMovimiento:
    if tipo == TipoRecompensa.cashback:
        return TipoMovimiento.cashback
    return TipoMovimiento.credito_tienda


def _raw_payload(datos: EcommerceOrderPaidRequest) -> dict[str, Any]:
    return datos.model_dump(mode="json")


def _event_metadata(event: EcommerceOrderEvent, datos: EcommerceOrderPaidRequest) -> dict[str, Any]:
    return {
        "ecommerce_event_id": event.id,
        "proveedor": event.proveedor,
        "external_order_id": event.external_order_id,
        "customer_email": event.customer_email,
        "amount": event.amount,
        "currency": event.currency,
        "metadata": datos.metadata or {},
    }


def _event_response(
    event: EcommerceOrderEvent,
    *,
    recompensa: AplicacionRecompensaResponse | None = None,
    movimiento: MovimientoResponse | None = None,
    mensaje: str,
) -> EcommerceOrderPaidResponse:
    return EcommerceOrderPaidResponse(
        event=EcommerceOrderEventResponse.model_validate(event),
        recompensa_aplicada=recompensa,
        movimiento=movimiento,
        mensaje=mensaje,
    )


def _duplicate_event_exists(db: Session, *, organizacion_id: UUID, proveedor: str, external_order_id: str) -> bool:
    existing = db.scalar(
        select(EcommerceOrderEvent.id).where(
            EcommerceOrderEvent.organizacion_id == organizacion_id,
            EcommerceOrderEvent.proveedor == proveedor,
            EcommerceOrderEvent.external_order_id == external_order_id,
        )
    )
    return existing is not None


def registrar_order_paid(
    datos: EcommerceOrderPaidRequest,
    context: APIKeyContext,
    db: Session,
) -> EcommerceOrderPaidResponse:
    organizacion = context.organizacion
    if organizacion.estado != EstadoOrganizacion.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizacion inactiva.")

    _validate_supported_currency(datos.currency)
    if _duplicate_event_exists(
        db,
        organizacion_id=organizacion.id,
        proveedor=datos.proveedor,
        external_order_id=datos.external_order_id,
    ):
        _audit_api_key(
            db,
            evento="ecommerce.order_paid_duplicado",
            mensaje="Orden ecommerce duplicada.",
            organizacion_id=organizacion.id,
            actor_api_key_id=context.api_key.id,
            metadata={"proveedor": datos.proveedor, "external_order_id": datos.external_order_id},
            nivel="WARNING",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La orden ya fue procesada.")

    event = EcommerceOrderEvent(
        organizacion_id=organizacion.id,
        proveedor=datos.proveedor,
        external_order_id=datos.external_order_id,
        customer_email=normalize_email(str(datos.customer_email)),
        customer_name=datos.customer_name,
        amount=_amount(datos.amount),
        currency=datos.currency,
        status="paid",
        raw_payload=_raw_payload(datos),
        procesado=False,
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        _audit_api_key(
            db,
            evento="ecommerce.order_paid_duplicado",
            mensaje="Orden ecommerce duplicada.",
            organizacion_id=organizacion.id,
            actor_api_key_id=context.api_key.id,
            metadata={"proveedor": datos.proveedor, "external_order_id": datos.external_order_id},
            nivel="WARNING",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La orden ya fue procesada.")

    _audit_api_key(
        db,
        evento="ecommerce.order_paid_recibido",
        mensaje="Orden ecommerce pagada recibida.",
        organizacion_id=organizacion.id,
        actor_api_key_id=context.api_key.id,
        metadata={"event_id": event.id, "proveedor": event.proveedor, "external_order_id": event.external_order_id},
    )
    return procesar_order_paid(event, datos, context, db)


def procesar_order_paid(
    event: EcommerceOrderEvent,
    datos: EcommerceOrderPaidRequest,
    context: APIKeyContext,
    db: Session,
) -> EcommerceOrderPaidResponse:
    try:
        usuario, cliente_creado = obtener_o_crear_cliente_ecommerce(datos, context, db)
        wallet_inicial_creada = _ensure_customer_primary_wallet(
            usuario,
            context,
            db,
            moneda=_validate_supported_currency(datos.currency),
        )
        regla = _find_applicable_rule(db, organizacion_id=context.organizacion.id, monto_compra=_amount(datos.amount))
        if regla is None:
            response = _mark_event_failed(
                db,
                event_id=event.id,
                message=NO_REWARD_RULE_MESSAGE,
                context=context,
            )
            _audit_customer_side_effects(
                db,
                context=context,
                usuario=usuario,
                cliente_creado=cliente_creado,
                wallet_creada=wallet_inicial_creada,
            )
            return response

        wallet, reward_wallet_creada = _obtener_o_crear_wallet_recompensa(usuario, regla, context, db)
        result = _aplicar_recompensa_ecommerce(event, datos, usuario, wallet, regla, context, db)
    except EcommerceProcessingError as exc:
        return _mark_event_failed(db, event_id=event.id, message=exc.message, context=context)
    except HTTPException as exc:
        message = str(exc.detail)
        return _mark_event_failed(db, event_id=event.id, message=message, context=context)

    _audit_customer_side_effects(
        db,
        context=context,
        usuario=usuario,
        cliente_creado=cliente_creado,
        wallet_creada=wallet_inicial_creada or reward_wallet_creada,
    )
    _notificar_recompensa_cliente(
        db,
        organizacion_id=context.organizacion.id,
        usuario_id=usuario.id,
        aplicacion=result["aplicacion"],
        movimiento=result["movimiento"],
        event=event,
    )
    _audit_reward_result(
        db,
        context=context,
        event=event,
        aplicacion=result["aplicacion"],
        movimiento=result["movimiento"],
        regla=regla,
    )
    stored_event = db.get(EcommerceOrderEvent, event.id)
    if stored_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento ecommerce no encontrado.")
    return _event_response(
        stored_event,
        recompensa=result["aplicacion"],
        movimiento=result["movimiento"],
        mensaje="Recompensa aplicada por compra ecommerce.",
    )


def obtener_o_crear_cliente_ecommerce(
    datos: EcommerceOrderPaidRequest,
    context: APIKeyContext,
    db: Session,
) -> tuple[Usuario, bool]:
    email = normalize_email(str(datos.customer_email))
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is not None:
        if usuario.organizacion_id != context.organizacion.id:
            raise EcommerceProcessingError("El email pertenece a otra organizacion.")
        if not usuario.es_activo:
            raise EcommerceProcessingError("El cliente esta inactivo.")
        return usuario, False

    validar_limite_usuarios(db, context.organizacion.id)
    usuario = Usuario(
        nombre=datos.customer_name or email,
        email=email,
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        es_activo=True,
        rol=RolUsuario.cliente,
        organizacion_id=context.organizacion.id,
    )
    db.add(usuario)
    db.flush()
    return usuario, True


def _ensure_customer_primary_wallet(
    usuario: Usuario,
    context: APIKeyContext,
    db: Session,
    *,
    moneda: MonedaWallet,
) -> bool:
    existing = db.scalar(
        select(Wallet.id).where(
            Wallet.owner_type == OwnerTypeWallet.usuario,
            Wallet.usuario_id == usuario.id,
            Wallet.organizacion_id == context.organizacion.id,
            Wallet.es_principal.is_(True),
            Wallet.estado != EstadoWallet.cerrada,
        )
    )
    if existing is not None:
        return False

    validar_limite_wallets(db, context.organizacion.id)
    wallet = Wallet(
        alias="Wallet ecommerce",
        tipo=TipoWallet.principal,
        estado=EstadoWallet.activa,
        moneda=moneda,
        saldo=Decimal("0.00"),
        es_principal=True,
        owner_type=OwnerTypeWallet.usuario,
        usuario_id=usuario.id,
        organizacion_owner_id=None,
        organizacion_id=context.organizacion.id,
    )
    db.add(wallet)
    db.flush()
    return True


def _obtener_o_crear_wallet_recompensa(
    usuario: Usuario,
    regla: ReglaRecompensa,
    context: APIKeyContext,
    db: Session,
) -> tuple[Wallet, bool]:
    moneda = _reward_currency_to_wallet_currency(regla.moneda_recompensa)
    wallet = db.scalar(
        select(Wallet)
        .where(
            Wallet.owner_type == OwnerTypeWallet.usuario,
            Wallet.usuario_id == usuario.id,
            Wallet.organizacion_id == context.organizacion.id,
            Wallet.moneda == moneda,
            Wallet.estado == EstadoWallet.activa,
        )
        .order_by(Wallet.es_principal.desc(), Wallet.fecha_creacion.asc())
        .with_for_update()
    )
    if wallet is not None:
        return wallet, False

    has_wallet = (
        db.scalar(
            select(Wallet.id).where(
                Wallet.owner_type == OwnerTypeWallet.usuario,
                Wallet.usuario_id == usuario.id,
                Wallet.organizacion_id == context.organizacion.id,
                Wallet.estado != EstadoWallet.cerrada,
            )
        )
        is not None
    )
    validar_limite_wallets(db, context.organizacion.id)
    wallet = Wallet(
        alias=f"Recompensas ecommerce {moneda.value}",
        tipo=TipoWallet.recompensas if has_wallet else TipoWallet.principal,
        estado=EstadoWallet.activa,
        moneda=moneda,
        saldo=Decimal("0.00"),
        es_principal=not has_wallet,
        owner_type=OwnerTypeWallet.usuario,
        usuario_id=usuario.id,
        organizacion_owner_id=None,
        organizacion_id=context.organizacion.id,
    )
    db.add(wallet)
    db.flush()
    return wallet, True


def _find_applicable_rule(db: Session, *, organizacion_id: UUID, monto_compra: Decimal) -> ReglaRecompensa | None:
    now = _now()
    reglas = db.scalars(
        select(ReglaRecompensa)
        .where(ReglaRecompensa.organizacion_id == organizacion_id)
        .order_by(ReglaRecompensa.fecha_creacion.asc(), ReglaRecompensa.id.asc())
    ).all()
    for regla in reglas:
        if _evaluate_rule(regla, monto_compra, now=now):
            return regla
    return None


def _evaluate_rule(regla: ReglaRecompensa, monto_compra: Decimal, *, now: datetime) -> bool:
    if regla.estado != EstadoReglaRecompensa.activa:
        return False
    if regla.monto_minimo_compra is not None and monto_compra < _amount(regla.monto_minimo_compra):
        return False
    fecha_inicio = _as_utc(regla.fecha_inicio)
    fecha_fin = _as_utc(regla.fecha_fin)
    if fecha_inicio is not None and now < fecha_inicio:
        return False
    if fecha_fin is not None and now > fecha_fin:
        return False
    return _calculate_reward(regla, monto_compra) > Decimal("0.00")


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


def _aplicar_recompensa_ecommerce(
    event: EcommerceOrderEvent,
    datos: EcommerceOrderPaidRequest,
    usuario: Usuario,
    wallet: Wallet,
    regla: ReglaRecompensa,
    context: APIKeyContext,
    db: Session,
) -> dict[str, AplicacionRecompensaResponse | MovimientoResponse]:
    locked_wallet = wallet
    if wallet.id is not None:
        locked_wallet = db.scalar(select(Wallet).where(Wallet.id == wallet.id).with_for_update())
        if locked_wallet is None:
            raise EcommerceProcessingError("Wallet de recompensa no encontrada.")

    if locked_wallet.owner_type != OwnerTypeWallet.usuario or locked_wallet.usuario_id != usuario.id:
        raise EcommerceProcessingError("La wallet de recompensa no pertenece al cliente.")
    if locked_wallet.organizacion_id != context.organizacion.id:
        raise EcommerceProcessingError("No se puede operar entre organizaciones.")
    if locked_wallet.estado != EstadoWallet.activa:
        raise EcommerceProcessingError("La wallet de recompensa no esta activa.")

    moneda = _reward_currency_to_wallet_currency(regla.moneda_recompensa)
    if locked_wallet.moneda != moneda:
        raise EcommerceProcessingError("La moneda de la wallet no coincide con la recompensa.")

    monto_compra = _amount(datos.amount)
    monto_recompensa = _calculate_reward(regla, monto_compra)
    if monto_recompensa <= Decimal("0.00"):
        raise EcommerceProcessingError(NO_REWARD_RULE_MESSAGE)

    validar_limite_movimientos_mes(db, context.organizacion.id)
    locked_wallet.saldo = _amount(locked_wallet.saldo) + monto_recompensa
    metadata = _json_metadata(
        {
            **_event_metadata(event, datos),
            "regla_id": regla.id,
            "tipo_recompensa": regla.tipo.value,
            "moneda_recompensa": regla.moneda_recompensa.value,
            "monto_compra": str(monto_compra),
        }
    )
    referencia = f"ecommerce:{event.id}"
    movimiento = Movimiento(
        wallet_origen_id=None,
        wallet_destino_id=locked_wallet.id,
        organizacion_id=context.organizacion.id,
        monto=monto_recompensa,
        moneda=moneda,
        tipo=_movement_type_for_reward(regla.tipo),
        estado=EstadoMovimiento.aprobada,
        descripcion=f"Recompensa ecommerce: {regla.nombre}",
        referencia_externa=referencia,
        metadata_movimiento=metadata,
        es_reversa=False,
    )
    db.add_all([locked_wallet, movimiento])
    try:
        db.flush()
        aplicacion = AplicacionRecompensa(
            organizacion_id=context.organizacion.id,
            regla_id=regla.id,
            usuario_id=usuario.id,
            wallet_destino_id=locked_wallet.id,
            movimiento_id=movimiento.id,
            monto_compra=monto_compra,
            monto_recompensa=monto_recompensa,
            moneda_recompensa=regla.moneda_recompensa,
            referencia_externa=referencia,
            metadata_aplicacion=metadata,
        )
        db.add(aplicacion)
        db.flush()
        event.procesado = True
        event.recompensa_aplicada_id = aplicacion.id
        event.error_procesamiento = None
        event.fecha_procesamiento = _now()
        db.add(event)
        db.commit()
        db.refresh(aplicacion)
        db.refresh(movimiento)
    except IntegrityError:
        db.rollback()
        raise EcommerceProcessingError("La orden ya fue procesada.")
    except Exception:
        db.rollback()
        raise

    return {
        "aplicacion": AplicacionRecompensaResponse.model_validate(aplicacion),
        "movimiento": MovimientoResponse.model_validate(movimiento),
    }


def _mark_event_failed(
    db: Session,
    *,
    event_id: UUID,
    message: str,
    context: APIKeyContext,
) -> EcommerceOrderPaidResponse:
    event = db.get(EcommerceOrderEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento ecommerce no encontrado.")
    event.procesado = True
    event.error_procesamiento = message
    event.fecha_procesamiento = _now()
    db.add(event)
    db.commit()
    db.refresh(event)
    _audit_api_key(
        db,
        evento="ecommerce.order_paid_error",
        mensaje="Orden ecommerce procesada con error.",
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        metadata={"event_id": event.id, "error": message, "external_order_id": event.external_order_id},
        nivel="ERROR",
    )
    return _event_response(event, mensaje=message)


def _audit_customer_side_effects(
    db: Session,
    *,
    context: APIKeyContext,
    usuario: Usuario,
    cliente_creado: bool,
    wallet_creada: bool,
) -> None:
    if cliente_creado:
        _audit_api_key(
            db,
            evento="ecommerce.cliente_creado_automaticamente",
            mensaje="Cliente ecommerce creado automaticamente.",
            organizacion_id=context.organizacion.id,
            actor_api_key_id=context.api_key.id,
            metadata={"usuario_id": usuario.id, "email": usuario.email},
        )
    if wallet_creada:
        _audit_api_key(
            db,
            evento="ecommerce.wallet_cliente_creada",
            mensaje="Wallet de cliente ecommerce creada.",
            organizacion_id=context.organizacion.id,
            actor_api_key_id=context.api_key.id,
            metadata={"usuario_id": usuario.id},
        )


def _notificar_recompensa_cliente(
    db: Session,
    *,
    organizacion_id: UUID,
    usuario_id: UUID,
    aplicacion: AplicacionRecompensaResponse,
    movimiento: MovimientoResponse,
    event: EcommerceOrderEvent,
) -> None:
    try:
        crear_notificacion_interna(
            organizacion_id=organizacion_id,
            usuario_id=usuario_id,
            tipo=TipoNotificacion.recompensa_aplicada,
            titulo="Recompensa recibida",
            mensaje="Recibiste una recompensa por tu compra.",
            db=db,
            metadata={
                "ecommerce_event_id": event.id,
                "aplicacion_id": aplicacion.id,
                "movimiento_id": movimiento.id,
                "external_order_id": event.external_order_id,
                "monto_recompensa": str(aplicacion.monto_recompensa),
                "moneda_recompensa": aplicacion.moneda_recompensa.value,
            },
        )
    except Exception:
        db.rollback()


def _audit_reward_result(
    db: Session,
    *,
    context: APIKeyContext,
    event: EcommerceOrderEvent,
    aplicacion: AplicacionRecompensaResponse,
    movimiento: MovimientoResponse,
    regla: ReglaRecompensa,
) -> None:
    metadata = {
        "event_id": event.id,
        "aplicacion_id": aplicacion.id,
        "movimiento_id": movimiento.id,
        "regla_id": regla.id,
        "external_order_id": event.external_order_id,
        "monto_compra": str(aplicacion.monto_compra),
        "monto_recompensa": str(aplicacion.monto_recompensa),
        "wallet_destino_id": aplicacion.wallet_destino_id,
        "usuario_id": aplicacion.usuario_id,
    }
    _audit_api_key(
        db,
        evento="movimiento_registrado",
        mensaje=f"Movimiento {movimiento.tipo.value} registrado.",
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        metadata={
            "movimiento_id": movimiento.id,
            "tipo_operacion": movimiento.tipo.value,
            "monto": str(movimiento.monto),
            "moneda": movimiento.moneda.value,
            "wallet_destino_id": movimiento.wallet_destino_id,
        },
    )
    _audit_api_key(
        db,
        evento="recompensa_aplicada",
        mensaje="Recompensa aplicada.",
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        metadata=metadata,
    )
    _audit_api_key(
        db,
        evento="ecommerce.order_paid_procesado",
        mensaje="Orden ecommerce procesada.",
        organizacion_id=context.organizacion.id,
        actor_api_key_id=context.api_key.id,
        metadata=metadata,
    )


def listar_order_events(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[EcommerceOrderEventResponse]:
    ensure_can_read_ecommerce(current_user)
    query = select(EcommerceOrderEvent)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(EcommerceOrderEvent.organizacion_id == organizacion_id)
    else:
        scope_id = resolve_organization_scope(current_user, organizacion_id)
        query = query.where(EcommerceOrderEvent.organizacion_id == scope_id)
    events = db.scalars(
        query.order_by(EcommerceOrderEvent.fecha_creacion.desc()).offset(skip).limit(limit)
    ).all()
    return [EcommerceOrderEventResponse.model_validate(event) for event in events]


def obtener_order_event(
    event_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> EcommerceOrderEventResponse:
    ensure_can_read_ecommerce(current_user)
    event = db.get(EcommerceOrderEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento ecommerce no encontrado.")
    if not is_super_admin(current_user.rol) and event.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento ecommerce no encontrado.")
    return EcommerceOrderEventResponse.model_validate(event)
