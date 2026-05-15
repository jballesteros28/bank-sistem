from __future__ import annotations

import html
import smtplib
from email.message import EmailMessage
from pathlib import Path
from string import Template
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.apps.notificaciones.services import registrar_envio_exitoso, registrar_error_envio
from app.core.config import settings
from app.core.database import SessionLocal


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _silent_mode() -> bool:
    return (
        not settings.EMAILS_ENABLED
        or settings.ENVIRONMENT.lower() in {"test", "testing"}
        or not settings.MAIL_FROM
        or not settings.MAIL_SERVER
    )


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    base = (TEMPLATE_DIR / "base.html").read_text(encoding="utf-8")
    content = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    safe_context = {key: html.escape(str(value)) for key, value in context.items() if value is not None}
    safe_context.setdefault("logo_block", "")
    if context.get("logo_url"):
        safe_context["logo_block"] = (
            f'<img src="{html.escape(str(context["logo_url"]))}" alt="{safe_context.get("nombre_organizacion", "")}" '
            'style="max-height:48px; margin-bottom:16px;" />'
        )
    body = Template(content).safe_substitute(safe_context)
    return Template(base).safe_substitute({**safe_context, "content": body})


def enviar_email(destinatario: str, asunto: str, html_body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.MAIL_FROM
    message["To"] = destinatario
    message["Subject"] = asunto
    message.set_content("Este mensaje requiere un cliente compatible con HTML.")
    message.add_alternative(html_body, subtype="html")

    if settings.MAIL_SSL_TLS:
        with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
            if settings.MAIL_USERNAME:
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
        if settings.MAIL_STARTTLS:
            smtp.starttls()
        if settings.MAIL_USERNAME:
            smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        smtp.send_message(message)


def _with_session(callback: Any) -> None:
    db: Session = SessionLocal()
    try:
        callback(db)
    finally:
        db.close()


def enviar_email_template(
    notificacion_id: UUID,
    destinatario: str,
    asunto: str,
    template_name: str,
    context: dict[str, Any],
) -> None:
    if _silent_mode():
        return
    try:
        html_body = _render_template(template_name, context)
        enviar_email(destinatario, asunto, html_body)
    except Exception as exc:
        try:
            _with_session(lambda db: registrar_error_envio(notificacion_id, str(exc), db))
        except Exception:
            pass
        return
    try:
        _with_session(lambda db: registrar_envio_exitoso(notificacion_id, db))
    except Exception:
        pass


def enviar_email_bienvenida_owner(
    notificacion_id: UUID,
    destinatario: str,
    context: dict[str, Any],
) -> None:
    enviar_email_template(notificacion_id, destinatario, "Organizacion creada correctamente", "onboarding_exitoso.html", context)


def enviar_email_movimiento(
    notificacion_id: UUID,
    destinatario: str,
    asunto: str,
    context: dict[str, Any],
) -> None:
    enviar_email_template(notificacion_id, destinatario, asunto, "movimiento.html", context)


def enviar_email_wallet_congelada(
    notificacion_id: UUID,
    destinatario: str,
    context: dict[str, Any],
) -> None:
    enviar_email_template(notificacion_id, destinatario, "Wallet congelada", "wallet_congelada.html", context)


def enviar_email_organizacion_suspendida(
    notificacion_id: UUID,
    destinatario: str,
    context: dict[str, Any],
) -> None:
    enviar_email_template(
        notificacion_id,
        destinatario,
        "Organizacion suspendida",
        "organizacion_suspendida.html",
        context,
    )
