# core/email.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from core.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict, Any

# ──────────────────────────────────────────────────────────────
# 📧 Configuración de conexión SMTP con FastAPI-Mail
# ──────────────────────────────────────────────────────────────
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="Sistema Bancario",   # Branding por defecto
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# ──────────────────────────────────────────────────────────────
# 🧠 Cargar entorno Jinja2 (versión robusta)
# 1) core/email/templates (tu caso actual)
# 2) <root>/templates (si en el futuro movés plantillas globales)
# 3) fallback → crea core/email/templates si no existe
# ──────────────────────────────────────────────────────────────
_current_dir = Path(__file__).resolve().parent       # -> core/email/
_candidates = [
    _current_dir / "templates",                      # core/email/templates
    _current_dir.parent.parent / "templates",        # <root>/templates
]

for _p in _candidates:
    if _p.exists():
        template_dir = _p
        break
else:
    # Último recurso: crear la carpeta local
    template_dir = _current_dir / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(["html", "xml"])
)

# ──────────────────────────────────────────────────────────────
# ✉️ Función principal para enviar correo HTML
# ──────────────────────────────────────────────────────────────
async def enviar_correo_html(
    destinatario: EmailStr,
    asunto: str,
    plantilla_html: str,
    contexto: Dict[str, Any]
) -> None:
    """
    Renderiza una plantilla HTML con variables dinámicas
    y envía un correo al destinatario.
    """
    try:
        # Cargar plantilla y renderizar con contexto
        template = env.get_template(plantilla_html)
        html_content = template.render(contexto)

        # Preparar el mensaje
        mensaje = MessageSchema(
            subject=asunto,
            recipients=[destinatario],
            body=html_content,
            subtype="html"
        )

        # Enviar correo
        fm = FastMail(conf)
        await fm.send_message(mensaje)

    except Exception as exc:
        # Si algo falla, propaga el error con detalle
        raise RuntimeError(
            f"Error enviando correo con plantilla '{plantilla_html}': {exc}"
        ) from exc
