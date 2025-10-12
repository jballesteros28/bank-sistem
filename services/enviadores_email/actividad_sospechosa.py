from services.email_service import enviar_email
from pydantic import EmailStr

# ⚠️ Notificación de actividad sospechosa
async def enviar_email_actividad_sospechosa(nombre: str, email: EmailStr, evento: str, fecha: str, ip: str):
    await enviar_email(
        destinatarios=[email],
        asunto="⚠️ Actividad sospechosa detectada",
        template_html="actividad_sospechosa.html",
        contexto={
            "nombre_usuario": nombre,
            "evento": evento,
            "fecha": fecha,
            "ip": ip
        }
    )
