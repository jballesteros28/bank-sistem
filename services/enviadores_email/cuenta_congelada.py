from pydantic import EmailStr
from services.email_service import enviar_email

async def enviar_email_cuenta_congelada(
    email: EmailStr,
    nombre: str,
    numero_cuenta: str,
    motivo: str | None = None
) -> None:
    await enviar_email(
        asunto="Tu cuenta ha cambiado de estado",
        destinatarios=[email],
        template_html="cuenta_congelada.html",
        contexto={
            "nombre": nombre,
            "numero_cuenta": numero_cuenta,
            "motivo": motivo or "Medidas de seguridad",
        },
    )