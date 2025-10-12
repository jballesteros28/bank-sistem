from services.email_service import enviar_email
from pydantic import EmailStr

# ✉️ Email genérico reutilizable
async def enviar_email_base(destinatario: EmailStr, asunto: str, titulo: str, mensaje: str, destacado: str = "", accion_url: str = "", accion_texto: str = ""):
    await enviar_email(
        destinatarios=[destinatario],
        asunto=asunto,
        template_html="base_email.html",
        contexto={
            "titulo": titulo,
            "mensaje": mensaje,
            "destacado": destacado,
            "accion_url": accion_url,
            "accion_texto": accion_texto
        }
    )
