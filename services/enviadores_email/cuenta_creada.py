from services.email_service import enviar_email
from pydantic import EmailStr
from typing import Any
from decimal import Decimal

async def enviar_email_cuenta_creada(
    email: EmailStr,
    nombre: str,
    numero_cuenta: str,
    tipo_cuenta: str,
    saldo_inicial: Decimal,
    estado: str,
) -> None:
    """
    Envía un correo notificando al usuario que su cuenta fue creada exitosamente.
    """
    contexto: dict[str, Any] = {
        "nombre": nombre,
        "numero_cuenta": numero_cuenta,
        "tipo_cuenta": tipo_cuenta,
        "saldo_inicial": saldo_inicial,
        "estado": estado,
        "url_portal": "https://sophiabank.com/portal",   # 🔗 personalizable
        "url_contacto": "https://sophiabank.com/contacto"
    }

    await enviar_email(
        asunto="Tu nueva cuenta ha sido creada",
        destinatarios=[email],
        template_html="cuenta_creada.html",
        contexto=contexto,
    )
