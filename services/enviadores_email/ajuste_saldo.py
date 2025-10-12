from pydantic import EmailStr
from services.email_service import enviar_email
from decimal import Decimal


async def enviar_email_ajuste_saldo(
    email: EmailStr,
    nombre: str,
    numero_cuenta: str,
    saldo_anterior: Decimal,
    saldo_nuevo: Decimal
) -> None:
    await enviar_email(
        asunto="Ajuste de saldo en tu cuenta",
        destinatarios=[email],
        template_html="ajuste_saldo.html",
        contexto={
            "nombre": nombre,
            "numero_cuenta": numero_cuenta,
            "saldo_anterior": saldo_anterior,
            "saldo_nuevo": saldo_nuevo,
        },
    )