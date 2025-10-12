from services.email_service import enviar_email
from pydantic import EmailStr
from decimal import Decimal
async def enviar_email_transferencia_exitosa(
    email: EmailStr,
    nombre: str,
    id_transaccion: int,
    monto: Decimal,
    cuenta_origen: int,
    cuenta_destino: int,
    fecha: str,
    descripcion: str
):
    await enviar_email(
        destinatarios= [email],
        asunto= "💸 Transferencia exitosa",
        template_html= "transferencia_exitosa.html",
        contexto= {
            "nombre_usuario": nombre,
            "id_transaccion": id_transaccion,
            "monto": monto,
            "cuenta_origen": cuenta_origen,
            "cuenta_destino": cuenta_destino,
            "fecha": fecha,
            "descripcion": descripcion
        }
    )
