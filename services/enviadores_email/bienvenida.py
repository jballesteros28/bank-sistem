from services.email_service import enviar_email
from pydantic import EmailStr

# 👋 Email de bienvenida luego del registro
async def enviar_email_bienvenida(nombre: str, email: EmailStr):
    await enviar_email(
        destinatarios=[email],
        asunto="👋 ¡Bienvenido a Banco Sophia!",
        template_html="bienvenida.html",
        contexto={
            "nombre_usuario": nombre
        }
    )