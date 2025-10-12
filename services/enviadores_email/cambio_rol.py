from pydantic import EmailStr
from services.email_service import enviar_email

async def enviar_email_cambio_rol(
    email: EmailStr,
    nombre: str,
    rol_anterior: str,
    rol_nuevo: str
) -> None:
    await enviar_email(
        asunto="Actualización de rol en tu cuenta",
        destinatarios=[email],
        template_html="cambio_rol.html",
        contexto={
            "nombre": nombre,
            "rol_anterior": rol_anterior,
            "rol_nuevo": rol_nuevo,
        },
    )