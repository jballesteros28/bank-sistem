# services/email_service.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from core.config import settings
from pydantic import EmailStr
from typing import Dict, Any
import os
from models.log import LogCorreo
from services.log_service import guardar_log_correo
from core.enums import EstadoNotificacion
from schemas.notificacion import NotificationCreate

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=os.path.join(os.getcwd(), "core", "email", "templates")
)

fm = FastMail(conf)


# 📤 Función reutilizable para enviar emails HTML con log en Mongo
async def enviar_email(
    asunto: str,
    destinatarios: list[EmailStr],
    template_html: str,
    contexto: Dict[Any, Any]
) -> None:
    mensaje = MessageSchema(
        subject=asunto,
        recipients=destinatarios,
        template_body=contexto,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(mensaje, template_name=template_html)

        # ✅ Guardar log de éxito
        log = LogCorreo(
            destinatario=",".join(destinatarios),
            asunto=asunto,
            template=template_html,
            estado="ENVIADO"
        )
        await guardar_log_correo(log)

    except Exception as e:
        # ❌ Guardar log de error
        log = LogCorreo(
            destinatario=",".join(destinatarios),
            asunto=asunto,
            template=template_html,
            estado="ERROR",
            error=str(e)
        )
        await guardar_log_correo(log)
        print(f"[ERROR] Fallo envío de correo: {e}")


# 📝 Guardar notificación en estado inicial (QUEUED)
async def log_notificacion(notification: NotificationCreate, estado: EstadoNotificacion) -> str:
    """
    Crea un log en Mongo para marcar la notificación como encolada (QUEUED).
    Devuelve el ID del log insertado.
    """
    log = LogCorreo(
        destinatario=notification.to_email,
        asunto=notification.subject,
        template=notification.template,
        estado=estado.value
    )
    log_id = await guardar_log_correo(log)
    return str(log_id)
