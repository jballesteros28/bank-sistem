# app/notificaciones/routes.py
from fastapi import APIRouter, BackgroundTasks, status
from schemas.notificacion import (
    BienvenidaIn,
    TransferenciaExitosaIn,
    ActividadSospechosaIn,
    ResetPasswordIn,
    NotificationCreate,
    NotificationOut,
)
from core.enums import TipoNotificacion, EstadoNotificacion
from services.enviadores_email import (
    bienvenida,
    transferencia_exitosa,
    actividad_sospechosa,
    reset_password,
)
from services.email_service import log_notificacion  # logging en Mongo

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

# ─────────────────────────────────────────────
# Bienvenida
# ─────────────────────────────────────────────
@router.post("/bienvenida", response_model=NotificationOut, status_code=status.HTTP_202_ACCEPTED)
async def enviar_bienvenida(payload: BienvenidaIn, background: BackgroundTasks) -> NotificationOut:
    notification = NotificationCreate(
        to_email=payload.email,
        subject="¡Bienvenido al Sistema Bancario!",
        template="bienvenida.html",
        context={"nombre": payload.nombre},
        tipo=TipoNotificacion.WELCOME,
    )
    doc_id = await log_notificacion(notification, EstadoNotificacion.QUEUED)
    background.add_task(bienvenida.enviar_email_bienvenida, nombre=payload.nombre, email=payload.email)
    return NotificationOut(id=str(doc_id),
                        to_email=payload.email,
                        subject=notification.subject,
                        tipo=notification.tipo,
                        status=EstadoNotificacion.QUEUED)

# ─────────────────────────────────────────────
# Transferencia Exitosa
# ─────────────────────────────────────────────
@router.post("/transferencia-exitosa", response_model=NotificationOut, status_code=status.HTTP_202_ACCEPTED)
async def enviar_transferencia_exitosa(payload: TransferenciaExitosaIn, background: BackgroundTasks) -> NotificationOut:
    notification = NotificationCreate(
        to_email=payload.email,
        subject="Confirmación de Transferencia Exitosa",
        template="transferencia_exitosa.html",
        context=payload.model_dump(),
        tipo=TipoNotificacion.TRANSFER_CONFIRMATION,
    )
    doc_id = await log_notificacion(notification, EstadoNotificacion.QUEUED)
    background.add_task(transferencia_exitosa.enviar_email_transferencia_exitosa, **payload.model_dump())
    return NotificationOut(id=str(doc_id),
                        to_email=payload.email,
                        subject=notification.subject,
                        tipo=notification.tipo,
                        status=EstadoNotificacion.QUEUED)

# ─────────────────────────────────────────────
# Actividad Sospechosa
# ─────────────────────────────────────────────
@router.post("/actividad-sospechosa", response_model=NotificationOut, status_code=status.HTTP_202_ACCEPTED)
async def enviar_actividad_sospechosa(payload: ActividadSospechosaIn, background: BackgroundTasks) -> NotificationOut:
    notification = NotificationCreate(
        to_email=payload.email,
        subject="Alerta de Actividad Sospechosa",
        template="actividad_sospechosa.html",
        context=payload.model_dump(),
        tipo=TipoNotificacion.GENERIC,
    )
    doc_id = await log_notificacion(notification, EstadoNotificacion.QUEUED)
    background.add_task(actividad_sospechosa.enviar_email_actividad_sospechosa, **payload.model_dump())
    return NotificationOut(id=str(doc_id),
                        to_email=payload.email,
                        subject=notification.subject,
                        tipo=notification.tipo,
                        status=EstadoNotificacion.QUEUED)

# ─────────────────────────────────────────────
# Reset Password
# ─────────────────────────────────────────────
@router.post("/reset-password", response_model=NotificationOut, status_code=status.HTTP_202_ACCEPTED)
async def enviar_reset_password(payload: ResetPasswordIn, background: BackgroundTasks) -> NotificationOut:
    notification = NotificationCreate(
        to_email=payload.email,
        subject="Recuperación de Contraseña",
        template="reset_password.html",
        context=payload.model_dump(),
        tipo=TipoNotificacion.PASSWORD_RESET,
    )
    doc_id = await log_notificacion(notification, EstadoNotificacion.QUEUED)
    background.add_task(reset_password.enviar_email_reset_password, **payload.model_dump())
    return NotificationOut(id=str(doc_id),
                        to_email=payload.email,
                        subject=notification.subject,
                        tipo=notification.tipo,
                        status=EstadoNotificacion.QUEUED)
