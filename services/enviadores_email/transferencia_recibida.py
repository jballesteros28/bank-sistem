from services.email_service import enviar_email
from pydantic import EmailStr
from typing import Any
from decimal import Decimal

async def enviar_email_transferencia_recibida(
    email: EmailStr,
    nombre: str,
    id_transaccion: int,
    monto: Decimal,
    cuenta_origen: int,
    cuenta_destino: int,
    fecha: str,
    descripcion: str = "",
) -> None:
    """
    Envía un correo notificando al receptor que recibió una transferencia.
    """
    contexto: dict[str, Any] = {
        "nombre": nombre,
        "id_transaccion": id_transaccion,
        "monto": monto,
        "cuenta_origen": cuenta_origen,
        "cuenta_destino": cuenta_destino,
        "fecha": fecha,
        "descripcion": descripcion,
        "url_portal": "https://sophiabank.com/portal",   # 🔗 personalizable
        "url_contacto": "https://sophiabank.com/contacto"
    }

    await enviar_email(
        asunto="Has recibido una nueva transferencia",
        destinatarios=[email],
        template_html="transferencia_recibida.html",
        contexto=contexto,
    )
