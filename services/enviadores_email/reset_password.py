# services/enviadores_email/reset_password.py
from pydantic import EmailStr
from services.email_service import enviar_email

# 📩 Envío de correo de recuperación de contraseña
async def enviar_email_reset_password(
    email: EmailStr,
    nombre: str,
    codigo: str
) -> None:
    """
    Envía un correo con el código de recuperación de contraseña.
    Usa la plantilla reset_password.html ubicada en core/email/templates/
    """
    contexto = {
        "nombre": nombre,
        "codigo": codigo
    }

    await enviar_email(
        asunto="Recuperación de Contraseña",
        destinatarios=[email],
        template_html="reset_password.html",
        contexto=contexto
    )
