from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.apps.auditoria.schemas import AuditLogCreate
from app.apps.auditoria.services import registrar_audit_log
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.movimientos.schemas import MovimientoResponse
from app.apps.notificaciones.models import Notificacion
from app.apps.notificaciones.schemas import (
    EmailTemplateContext,
    NotificacionCreate,
    NotificacionListResponse,
    NotificacionMarcarLeidaRequest,
    NotificacionResponse,
)
from app.apps.onboarding.schemas import OnboardingRegistroResponse
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.apps.wallets.schemas import WalletResponse
from app.core.permissions import is_admin, is_super_admin
from app.shared.enums import (
    CanalNotificacion,
    EstadoOrganizacion,
    EstadoWallet,
    RolUsuario,
    TipoMovimiento,
    TipoNotificacion,
)


MOVIMIENTO_TIPO_NOTIFICACION = {
    TipoMovimiento.deposito: TipoNotificacion.movimiento_deposito,
    TipoMovimiento.retiro: TipoNotificacion.movimiento_retiro,
    TipoMovimiento.transferencia: TipoNotificacion.movimiento_transferencia,
    TipoMovimiento.pago: TipoNotificacion.movimiento_pago,
    TipoMovimiento.cashback: TipoNotificacion.movimiento_cashback,
    TipoMovimiento.ajuste_admin: TipoNotificacion.movimiento_ajuste_admin,
    TipoMovimiento.reversa: TipoNotificacion.movimiento_reversa,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    evento: str,
    mensaje: str,
    organizacion_id: UUID | None,
    actor_usuario_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    nivel: str = "INFO",
) -> None:
    try:
        registrar_audit_log(
            AuditLogCreate(
                evento=evento,
                mensaje=mensaje,
                nivel=nivel,
                actor_usuario_id=actor_usuario_id,
                organizacion_id=organizacion_id,
                metadata=metadata,
            ),
            db,
        )
    except Exception:
        db.rollback()


def _brand_context(organizacion: Organizacion) -> dict[str, str | None]:
    return {
        "nombre_organizacion": organizacion.nombre_comercial or organizacion.nombre,
        "color_primario": organizacion.color_primario or "#0f766e",
        "logo_url": organizacion.logo_url,
    }


def _metadata(value: dict[str, Any] | None) -> dict[str, Any] | None:
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


def _persistir_notificacion(
    datos: NotificacionCreate,
    db: Session,
    *,
    actor_usuario_id: UUID | None = None,
) -> Notificacion:
    notificacion = Notificacion(
        organizacion_id=datos.organizacion_id,
        usuario_id=datos.usuario_id,
        tipo=datos.tipo,
        canal=datos.canal,
        titulo=datos.titulo,
        mensaje=datos.mensaje,
        metadata_notificacion=_metadata(datos.metadata),
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    _audit(
        db,
        evento="notificacion_creada",
        mensaje=f"Notificacion {notificacion.tipo.value} creada.",
        actor_usuario_id=actor_usuario_id,
        organizacion_id=notificacion.organizacion_id,
        metadata={"notificacion_id": str(notificacion.id), "canal": notificacion.canal.value},
    )
    return notificacion


def crear_notificacion_interna(
    *,
    organizacion_id: UUID,
    usuario_id: UUID | None,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    db: Session,
    metadata: dict[str, Any] | None = None,
    actor_usuario_id: UUID | None = None,
) -> NotificacionResponse:
    notificacion = _persistir_notificacion(
        NotificacionCreate(
            organizacion_id=organizacion_id,
            usuario_id=usuario_id,
            tipo=tipo,
            canal=CanalNotificacion.interna,
            titulo=titulo,
            mensaje=mensaje,
            metadata=metadata,
        ),
        db,
        actor_usuario_id=actor_usuario_id,
    )
    return NotificacionResponse.model_validate(notificacion)


def crear_notificacion_email(
    *,
    organizacion_id: UUID,
    usuario_id: UUID | None,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    destinatario: str,
    template_name: str,
    db: Session,
    metadata: dict[str, Any] | None = None,
    actor_usuario_id: UUID | None = None,
) -> Notificacion:
    datos_metadata = {**(metadata or {}), "destinatario": destinatario, "template": template_name}
    return _persistir_notificacion(
        NotificacionCreate(
            organizacion_id=organizacion_id,
            usuario_id=usuario_id,
            tipo=tipo,
            canal=CanalNotificacion.email,
            titulo=titulo,
            mensaje=mensaje,
            metadata=datos_metadata,
        ),
        db,
        actor_usuario_id=actor_usuario_id,
    )


def _agendar_email(
    background_tasks: BackgroundTasks | None,
    *,
    notificacion_id: UUID,
    destinatario: str,
    asunto: str,
    template_name: str,
    context: EmailTemplateContext,
) -> None:
    if background_tasks is None:
        return
    from app.apps.notificaciones.email_service import enviar_email_template

    background_tasks.add_task(
        enviar_email_template,
        notificacion_id,
        destinatario,
        asunto,
        template_name,
        context.model_dump(mode="json"),
    )


def crear_notificacion_y_email(
    *,
    organizacion: Organizacion,
    usuario: Usuario | None,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
    template_name: str = "base.html",
    metadata: dict[str, Any] | None = None,
    actor_usuario_id: UUID | None = None,
) -> NotificacionResponse:
    usuario_id = usuario.id if usuario is not None else None
    interna = crear_notificacion_interna(
        organizacion_id=organizacion.id,
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        db=db,
        metadata=metadata,
        actor_usuario_id=actor_usuario_id,
    )
    if usuario is None:
        return interna

    email = crear_notificacion_email(
        organizacion_id=organizacion.id,
        usuario_id=usuario.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        destinatario=usuario.email,
        template_name=template_name,
        db=db,
        metadata=metadata,
        actor_usuario_id=actor_usuario_id,
    )
    brand = _brand_context(organizacion)
    context = EmailTemplateContext(
        organizacion_id=organizacion.id,
        destinatario=usuario.email,
        asunto=titulo,
        titulo=titulo,
        mensaje=mensaje,
        nombre_organizacion=str(brand["nombre_organizacion"]),
        color_primario=str(brand["color_primario"]),
        logo_url=brand["logo_url"],
        metadata=_metadata(metadata) or {},
    )
    _agendar_email(
        background_tasks,
        notificacion_id=email.id,
        destinatario=usuario.email,
        asunto=titulo,
        template_name=template_name,
        context=context,
    )
    return interna


def _query_scoped(
    current_user: DatosUsuarioToken,
    organizacion_id: UUID | None = None,
    *,
    canal: CanalNotificacion = CanalNotificacion.interna,
) -> Any:
    query = select(Notificacion).where(Notificacion.canal == canal)
    if is_super_admin(current_user.rol):
        if organizacion_id is not None:
            query = query.where(Notificacion.organizacion_id == organizacion_id)
    elif is_admin(current_user.rol):
        if organizacion_id is not None and organizacion_id != current_user.organizacion_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes operar otra organizacion.")
        query = query.where(Notificacion.organizacion_id == current_user.organizacion_id)
    else:
        query = query.where(Notificacion.usuario_id == current_user.id)
    return query


def listar_notificaciones_usuario(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> NotificacionListResponse:
    query = _query_scoped(current_user, organizacion_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    unread_query = query.where(Notificacion.leida.is_(False))
    no_leidas = db.scalar(select(func.count()).select_from(unread_query.subquery())) or 0
    items = db.scalars(query.order_by(Notificacion.fecha_creacion.desc()).offset(skip).limit(limit)).all()
    return NotificacionListResponse(
        items=[NotificacionResponse.model_validate(item) for item in items],
        total=total,
        no_leidas=no_leidas,
    )


def listar_notificaciones_organizacion(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> NotificacionListResponse:
    if not is_admin(current_user.rol) and not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operacion restringida a administradores.")
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    return listar_notificaciones_usuario(current_user, db, scope_id, skip, limit)


def _get_notificacion_scoped(
    notificacion_id: UUID,
    current_user: DatosUsuarioToken,
    db: Session,
) -> Notificacion:
    query = _query_scoped(current_user).where(Notificacion.id == notificacion_id)
    notificacion = db.scalar(query)
    if notificacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificacion no encontrada.")
    return notificacion


def marcar_como_leida(
    notificacion_id: UUID,
    datos: NotificacionMarcarLeidaRequest,
    current_user: DatosUsuarioToken,
    db: Session,
) -> NotificacionResponse:
    notificacion = _get_notificacion_scoped(notificacion_id, current_user, db)
    notificacion.leida = datos.leida
    notificacion.fecha_lectura = _now() if datos.leida else None
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    _audit(
        db,
        evento="notificacion_marcada_leida",
        mensaje="Notificacion marcada como leida.",
        actor_usuario_id=current_user.id,
        organizacion_id=notificacion.organizacion_id,
        metadata={"notificacion_id": str(notificacion.id), "leida": notificacion.leida},
    )
    return NotificacionResponse.model_validate(notificacion)


def marcar_todas_como_leidas(current_user: DatosUsuarioToken, db: Session) -> int:
    query = _query_scoped(current_user).where(Notificacion.leida.is_(False))
    notificaciones = db.scalars(query).all()
    for notificacion in notificaciones:
        notificacion.leida = True
        notificacion.fecha_lectura = _now()
        db.add(notificacion)
    db.commit()
    _audit(
        db,
        evento="notificaciones_marcadas_leidas",
        mensaje="Notificaciones marcadas como leidas.",
        actor_usuario_id=current_user.id,
        organizacion_id=current_user.organizacion_id,
        metadata={"cantidad": len(notificaciones)},
    )
    return len(notificaciones)


def contar_no_leidas(current_user: DatosUsuarioToken, db: Session) -> int:
    query = _query_scoped(current_user).where(Notificacion.leida.is_(False))
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def registrar_envio_exitoso(notificacion_id: UUID, db: Session) -> None:
    notificacion = db.get(Notificacion, notificacion_id)
    if notificacion is None:
        return
    notificacion.enviada = True
    notificacion.error_envio = None
    notificacion.fecha_envio = _now()
    db.add(notificacion)
    db.commit()
    _audit(
        db,
        evento="email_enviado",
        mensaje="Email de evento enviado.",
        organizacion_id=notificacion.organizacion_id,
        metadata={"notificacion_id": str(notificacion.id), "tipo": notificacion.tipo.value},
    )


def registrar_error_envio(notificacion_id: UUID, error: str, db: Session) -> None:
    notificacion = db.get(Notificacion, notificacion_id)
    if notificacion is None:
        return
    notificacion.enviada = False
    notificacion.error_envio = error[:1000]
    db.add(notificacion)
    db.commit()
    _audit(
        db,
        evento="email_error",
        mensaje="Error al enviar email de evento.",
        organizacion_id=notificacion.organizacion_id,
        metadata={"notificacion_id": str(notificacion.id), "error": notificacion.error_envio},
        nivel="ERROR",
    )


def _safe_event(callback: Any) -> None:
    try:
        callback()
    except Exception:
        pass


def notificar_onboarding_exitoso(
    resultado: OnboardingRegistroResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, resultado.organizacion.id)
        owner = db.get(Usuario, resultado.owner.id)
        if organizacion is None or owner is None:
            return
        crear_notificacion_y_email(
            organizacion=organizacion,
            usuario=owner,
            tipo=TipoNotificacion.onboarding_exitoso,
            titulo="Organizacion creada correctamente",
            mensaje="Tu organizacion ya esta lista para operar en Wallet SaaS.",
            template_name="onboarding_exitoso.html",
            metadata={"organizacion_id": organizacion.id, "owner_id": owner.id},
            db=db,
            background_tasks=background_tasks,
            actor_usuario_id=owner.id,
        )

    _safe_event(_run)


def notificar_wallet_creada(
    wallet: WalletResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, wallet.organizacion_id)
        usuario = db.get(Usuario, wallet.usuario_id) if wallet.usuario_id is not None else None
        if organizacion is None or usuario is None:
            return
        crear_notificacion_y_email(
            organizacion=organizacion,
            usuario=usuario,
            tipo=TipoNotificacion.wallet_creada,
            titulo="Wallet creada",
            mensaje=f"Se creo la wallet {wallet.alias or wallet.id} en {wallet.moneda.value}.",
            template_name="wallet_creada.html",
            metadata={"wallet_id": wallet.id, "moneda": wallet.moneda.value},
            db=db,
            background_tasks=background_tasks,
            actor_usuario_id=actor_usuario_id,
        )

    _safe_event(_run)


def _usuarios_owner_admin(db: Session, organizacion_id: UUID) -> list[Usuario]:
    return db.scalars(
        select(Usuario).where(
            Usuario.organizacion_id == organizacion_id,
            or_(Usuario.rol == RolUsuario.owner, Usuario.rol == RolUsuario.admin),
        )
    ).all()


def notificar_wallet_organizacion_creada(
    wallet: WalletResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, wallet.organizacion_id)
        if organizacion is None:
            return
        usuarios = _usuarios_owner_admin(db, wallet.organizacion_id)
        metadata = {
            "wallet_id": wallet.id,
            "moneda": wallet.moneda.value,
            "owner_type": wallet.owner_type.value,
        }
        if not usuarios:
            crear_notificacion_y_email(
                organizacion=organizacion,
                usuario=None,
                tipo=TipoNotificacion.wallet_organizacion_creada,
                titulo="Wallet de organizacion creada",
                mensaje=f"Se creo la wallet {wallet.alias or wallet.id} en {wallet.moneda.value}.",
                template_name="wallet_creada.html",
                metadata=metadata,
                db=db,
                background_tasks=background_tasks,
                actor_usuario_id=actor_usuario_id,
            )
            return
        for usuario in usuarios:
            crear_notificacion_y_email(
                organizacion=organizacion,
                usuario=usuario,
                tipo=TipoNotificacion.wallet_organizacion_creada,
                titulo="Wallet de organizacion creada",
                mensaje=f"Se creo la wallet {wallet.alias or wallet.id} en {wallet.moneda.value}.",
                template_name="wallet_creada.html",
                metadata=metadata,
                db=db,
                background_tasks=background_tasks,
                actor_usuario_id=actor_usuario_id,
            )

    _safe_event(_run)


def notificar_wallet_congelada(
    wallet: WalletResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    if wallet.estado != EstadoWallet.congelada:
        return

    def _run() -> None:
        organizacion = db.get(Organizacion, wallet.organizacion_id)
        usuario = db.get(Usuario, wallet.usuario_id) if wallet.usuario_id is not None else None
        if organizacion is None or usuario is None:
            return
        crear_notificacion_y_email(
            organizacion=organizacion,
            usuario=usuario,
            tipo=TipoNotificacion.wallet_congelada,
            titulo="Wallet congelada",
            mensaje=f"La wallet {wallet.alias or wallet.id} fue congelada temporalmente.",
            template_name="wallet_congelada.html",
            metadata={"wallet_id": wallet.id},
            db=db,
            background_tasks=background_tasks,
            actor_usuario_id=actor_usuario_id,
        )

    _safe_event(_run)


def _usuarios_para_movimiento(movimiento: MovimientoResponse, db: Session) -> list[Usuario]:
    origen = db.get(Wallet, movimiento.wallet_origen_id) if movimiento.wallet_origen_id is not None else None
    destino = db.get(Wallet, movimiento.wallet_destino_id) if movimiento.wallet_destino_id is not None else None
    usuarios: list[Usuario] = []

    def add_wallet_owner(wallet: Wallet | None) -> None:
        if wallet is None or wallet.usuario_id is None:
            return
        usuario = db.get(Usuario, wallet.usuario_id)
        if usuario is not None and all(existing.id != usuario.id for existing in usuarios):
            usuarios.append(usuario)

    if movimiento.tipo in {TipoMovimiento.deposito, TipoMovimiento.cashback}:
        add_wallet_owner(destino)
    elif movimiento.tipo == TipoMovimiento.retiro:
        add_wallet_owner(origen)
    elif movimiento.tipo == TipoMovimiento.ajuste_admin:
        operation = (movimiento.metadata_movimiento or {}).get("operacion")
        add_wallet_owner(origen if operation == "debito" else destino)
    else:
        for wallet in (origen, destino):
            add_wallet_owner(wallet)
    return usuarios


def _texto_movimiento(movimiento: MovimientoResponse) -> tuple[str, str]:
    operation = (movimiento.metadata_movimiento or {}).get("operacion")
    if movimiento.tipo == TipoMovimiento.deposito:
        return "Deposito acreditado", "Se acreditó saldo en tu wallet."
    if movimiento.tipo == TipoMovimiento.retiro:
        return "Retiro debitado", "Se debitó saldo de tu wallet."
    if movimiento.tipo == TipoMovimiento.cashback:
        return "Cashback recibido", "Recibiste cashback."
    if movimiento.tipo == TipoMovimiento.ajuste_admin and operation == "debito":
        return "Ajuste administrativo", "Se debitó saldo de tu wallet por un ajuste administrativo."
    if movimiento.tipo == TipoMovimiento.ajuste_admin:
        return "Ajuste administrativo", "Se acreditó saldo en tu wallet por un ajuste administrativo."
    if movimiento.tipo == TipoMovimiento.reversa:
        return "Reversa registrada", "Se registró una reversa de movimiento."
    if movimiento.tipo == TipoMovimiento.transferencia:
        return "Transferencia registrada", "Se registró una transferencia."
    return "Pago registrado", "Se registró un pago."


def notificar_movimiento(
    movimiento: MovimientoResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, movimiento.organizacion_id)
        if organizacion is None:
            return
        tipo = MOVIMIENTO_TIPO_NOTIFICACION[movimiento.tipo]
        titulo, mensaje = _texto_movimiento(movimiento)
        metadata = {
            "movimiento_id": movimiento.id,
            "tipo": movimiento.tipo.value,
            "monto": str(movimiento.monto),
            "moneda": movimiento.moneda.value,
        }
        if movimiento.wallet_origen_id is not None:
            metadata["wallet_origen_id"] = movimiento.wallet_origen_id
        if movimiento.wallet_destino_id is not None:
            metadata["wallet_destino_id"] = movimiento.wallet_destino_id
        for usuario in _usuarios_para_movimiento(movimiento, db):
            crear_notificacion_y_email(
                organizacion=organizacion,
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                template_name="movimiento.html",
                metadata=metadata,
                db=db,
                background_tasks=background_tasks,
                actor_usuario_id=actor_usuario_id,
            )

    _safe_event(_run)


def notificar_pago_organizacion(
    movimiento: MovimientoResponse,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, movimiento.organizacion_id)
        origen = db.get(Wallet, movimiento.wallet_origen_id) if movimiento.wallet_origen_id is not None else None
        destino = db.get(Wallet, movimiento.wallet_destino_id) if movimiento.wallet_destino_id is not None else None
        if organizacion is None or origen is None or destino is None:
            return

        metadata = {
            "movimiento_id": movimiento.id,
            "tipo": movimiento.tipo.value,
            "monto": str(movimiento.monto),
            "moneda": movimiento.moneda.value,
            "wallet_origen_id": movimiento.wallet_origen_id,
            "wallet_destino_id": movimiento.wallet_destino_id,
        }
        if origen.usuario_id is not None:
            pagador = db.get(Usuario, origen.usuario_id)
            if pagador is not None:
                crear_notificacion_y_email(
                    organizacion=organizacion,
                    usuario=pagador,
                    tipo=TipoNotificacion.pago_organizacion_realizado,
                    titulo="Pago realizado",
                    mensaje=f"Se registro tu pago a la organizacion por {movimiento.monto}.",
                    template_name="movimiento.html",
                    metadata=metadata,
                    db=db,
                    background_tasks=background_tasks,
                    actor_usuario_id=actor_usuario_id,
                )

        usuarios = _usuarios_owner_admin(db, movimiento.organizacion_id)
        for usuario in usuarios:
            crear_notificacion_y_email(
                organizacion=organizacion,
                usuario=usuario,
                tipo=TipoNotificacion.pago_organizacion_recibido,
                titulo="Pago recibido",
                mensaje=f"La organizacion recibio un pago por {movimiento.monto}.",
                template_name="movimiento.html",
                metadata=metadata,
                db=db,
                background_tasks=background_tasks,
                actor_usuario_id=actor_usuario_id,
            )

    _safe_event(_run)


def notificar_organizacion_suspendida(
    organizacion_id: UUID,
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    actor_usuario_id: UUID | None = None,
) -> None:
    def _run() -> None:
        organizacion = db.get(Organizacion, organizacion_id)
        if organizacion is None or organizacion.estado != EstadoOrganizacion.suspendida:
            return
        usuarios = db.scalars(
            select(Usuario).where(
                Usuario.organizacion_id == organizacion.id,
                or_(Usuario.rol == RolUsuario.owner, Usuario.rol == RolUsuario.admin),
            )
        ).all()
        for usuario in usuarios:
            crear_notificacion_y_email(
                organizacion=organizacion,
                usuario=usuario,
                tipo=TipoNotificacion.organizacion_suspendida,
                titulo="Organizacion suspendida",
                mensaje="La organizacion fue suspendida. Contacta a soporte para revisar el estado.",
                template_name="organizacion_suspendida.html",
                metadata={"organizacion_id": organizacion.id},
                db=db,
                background_tasks=background_tasks,
                actor_usuario_id=actor_usuario_id,
            )

    _safe_event(_run)
