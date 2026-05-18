"""Seed demo idempotente para dejar Wallet SaaS listo para pruebas manuales.

No corre en produccion real por defecto: `main()` valida ENVIRONMENT,
ALLOW_DEMO_SEED y DATABASE_URL antes de abrir una sesion contra la base configurada.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import secrets
import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.apps.auditoria.models import AuditLog  # noqa: F401
from app.apps.ecommerce.models import EcommerceOrderEvent  # noqa: F401
from app.apps.integraciones.models import APIKey, WebhookDelivery, WebhookEndpoint  # noqa: F401
from app.apps.integraciones.services import encrypt_webhook_secret
from app.apps.movimientos.models import Movimiento
from app.apps.notificaciones.models import Notificacion
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.services import asegurar_planes_base, obtener_plan_por_codigo
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.shared.enums import (
    CanalNotificacion,
    EstadoMovimiento,
    EstadoOrganizacion,
    EstadoReglaRecompensa,
    EstadoWallet,
    MonedaRecompensa,
    MonedaWallet,
    OwnerTypeWallet,
    RolUsuario,
    TipoMovimiento,
    TipoNotificacion,
    TipoRecompensa,
    TipoWallet,
)
from app.shared.utils import normalize_email


DEMO_PASSWORD = "Password123!"
DEMO_ORG = {
    "nombre": "Demo Wallet",
    "slug": "demo-wallet",
    "email_contacto": "demo@example.com",
}
DEMO_OWNER = {
    "nombre": "Demo Owner",
    "email": "owner@demo.com",
}
DEMO_ADMIN = {
    "nombre": "Demo Admin",
    "email": "admin@demo.com",
}
DEMO_SUPPORT = {
    "nombre": "Demo Soporte",
    "email": "soporte@demo.com",
}
DEMO_SUPER_ADMIN = {
    "nombre": "Demo Super Admin",
    "email": "superadmin@demo.com",
}
DEMO_CLIENT = {
    "nombre": "Demo Cliente",
    "email": "cliente@demo.com",
}
DEMO_USERS = {
    "super_admin": {**DEMO_SUPER_ADMIN, "rol": RolUsuario.super_admin},
    "owner": {**DEMO_OWNER, "rol": RolUsuario.owner},
    "admin": {**DEMO_ADMIN, "rol": RolUsuario.admin},
    "soporte": {**DEMO_SUPPORT, "rol": RolUsuario.soporte},
    "cliente": {**DEMO_CLIENT, "rol": RolUsuario.cliente},
}
DEMO_API_KEY_NAME = "API Key Demo"
DEMO_API_KEY_SCOPES = [
    "wallets:read",
    "movimientos:read",
    "movimientos:write",
    "ecommerce:read",
    "ecommerce:write",
]
DEMO_WEBHOOK_NAME = "Webhook Demo"
DEMO_WEBHOOK_SECRET = "demo-webhook-secret"
DEMO_REWARD_RULE_NAME = "Cashback Demo 10%"
DEMO_REWARD_REFERENCE = "seed-recompensa-demo"
DEMO_ORG_BALANCE = Decimal("50000.00")
DEMO_CLIENT_BALANCE = Decimal("10000.00")
DEMO_OWNER_BALANCE = Decimal("5000.00")
DEMO_ADMIN_BALANCE = Decimal("3000.00")


def _masked_database_url() -> str:
    try:
        return make_url(settings.DATABASE_URL).render_as_string(hide_password=True)
    except Exception:
        return "<DATABASE_URL invalida>"


def _database_safety_issues() -> list[str]:
    allow_hosted_demo_database = (
        settings.ENVIRONMENT.strip().lower() == "production" and settings.ALLOW_DEMO_SEED
    )
    issues: list[str] = []
    try:
        url = make_url(settings.DATABASE_URL)
    except Exception as exc:
        return [f"No se pudo parsear DATABASE_URL: {exc}"]

    database_name = (url.database or "").lower()
    host = (url.host or "").lower()
    backend = url.get_backend_name()

    if allow_hosted_demo_database:
        if backend != "postgresql":
            issues.append("DATABASE_URL debe usar PostgreSQL para seed demo en production.")
        if not database_name:
            issues.append("DATABASE_URL debe incluir nombre de base para seed demo en production.")
        if not host:
            issues.append("DATABASE_URL debe incluir host para seed demo en production.")
        return issues

    if "wallet_saas" not in database_name:
        issues.append("El nombre de base en DATABASE_URL debe contener 'wallet_saas'.")
    if host not in {"localhost", "127.0.0.1", "postgres"}:
        issues.append("DATABASE_URL debe apuntar a localhost, 127.0.0.1 o al servicio Docker postgres.")
    return issues


def _ensure_dev_database_safety(*, allow_unsafe_database: bool = False) -> None:
    if settings.ENVIRONMENT.strip().lower() == "production":
        if not settings.ALLOW_DEMO_SEED:
            raise SystemExit(
                "Abortado: dev_seed.py no corre con ENVIRONMENT=production salvo que "
                "ALLOW_DEMO_SEED=true. Usar solo en entornos demo, nunca en produccion real."
            )
        print("ALLOW_DEMO_SEED=true detectado con ENVIRONMENT=production. Ejecutando seed demo controlado.")

    issues = _database_safety_issues()
    if not issues:
        return

    print("")
    print("ADVERTENCIA FUERTE: la base configurada no parece ser la base local de desarrollo.")
    print(f"ENVIRONMENT={settings.ENVIRONMENT}")
    print(f"DATABASE_URL={_masked_database_url()}")
    for issue in issues:
        print(f"- {issue}")
    if settings.ENVIRONMENT.strip().lower() == "production":
        raise SystemExit("Abortado por seguridad: DATABASE_URL no es valido para seed demo en production.")
    if not allow_unsafe_database:
        raise SystemExit(
            "Abortado por seguridad. Si realmente es una base local de desarrollo, "
            "reintenta con --allow-unsafe-database."
        )
    print("Continuando porque se paso --allow-unsafe-database.")


def _ensure_base_plans(db: Session) -> None:
    asegurar_planes_base(db, commit=False)


def _ensure_demo_organization(db: Session) -> Organizacion:
    _ensure_base_plans(db)
    starter_plan = obtener_plan_por_codigo("starter", db)
    if starter_plan is None:
        raise RuntimeError("Plan starter no disponible despues de asegurar planes base.")

    organizacion = db.scalar(select(Organizacion).where(Organizacion.slug == DEMO_ORG["slug"]))
    if organizacion is None:
        organizacion = Organizacion(slug=DEMO_ORG["slug"])
        db.add(organizacion)

    organizacion.nombre = DEMO_ORG["nombre"]
    organizacion.email_contacto = normalize_email(DEMO_ORG["email_contacto"])
    organizacion.nombre_comercial = DEMO_ORG["nombre"]
    organizacion.moneda_default = MonedaWallet.ARS.value
    organizacion.timezone = "America/Argentina/Buenos_Aires"
    organizacion.plan_id = starter_plan.id
    organizacion.estado = EstadoOrganizacion.activa
    db.flush()
    return organizacion


def _ensure_demo_users(db: Session, *, organizacion: Organizacion) -> dict[str, Usuario]:
    return {
        key: _ensure_user(
            db,
            organizacion=organizacion,
            nombre=str(user_data["nombre"]),
            email=str(user_data["email"]),
            rol=user_data["rol"],
        )
        for key, user_data in DEMO_USERS.items()
    }


def _ensure_user(
    db: Session,
    *,
    organizacion: Organizacion,
    nombre: str,
    email: str,
    rol: RolUsuario,
) -> Usuario:
    normalized_email = normalize_email(email)
    usuario = db.scalar(select(Usuario).where(Usuario.email == normalized_email))
    if usuario is None:
        usuario = Usuario(email=normalized_email)
        db.add(usuario)

    usuario.nombre = nombre
    usuario.hashed_password = hash_password(DEMO_PASSWORD)
    usuario.rol = rol
    usuario.es_activo = True
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.organizacion_id = organizacion.id
    db.flush()
    return usuario


def _ensure_user_wallet(
    db: Session,
    *,
    organizacion: Organizacion,
    usuario: Usuario,
    alias: str,
    saldo: Decimal,
) -> Wallet:
    wallet = db.scalar(
        select(Wallet).where(
            Wallet.owner_type == OwnerTypeWallet.usuario,
            Wallet.usuario_id == usuario.id,
            Wallet.organizacion_id == organizacion.id,
            Wallet.es_principal.is_(True),
            Wallet.estado != EstadoWallet.cerrada,
        )
    )
    if wallet is None:
        wallet = Wallet(
            owner_type=OwnerTypeWallet.usuario,
            usuario_id=usuario.id,
            organizacion_owner_id=None,
            organizacion_id=organizacion.id,
        )
        db.add(wallet)

    wallet.alias = alias
    wallet.tipo = TipoWallet.principal
    wallet.estado = EstadoWallet.activa
    wallet.moneda = MonedaWallet.ARS
    wallet.saldo = saldo
    wallet.limite_operacion = None
    wallet.es_principal = True
    db.flush()
    return wallet


def _ensure_organization_wallet(
    db: Session,
    *,
    organizacion: Organizacion,
    alias: str,
    saldo: Decimal,
) -> Wallet:
    wallet = db.scalar(
        select(Wallet).where(
            Wallet.owner_type == OwnerTypeWallet.organizacion,
            Wallet.organizacion_owner_id == organizacion.id,
            Wallet.organizacion_id == organizacion.id,
            Wallet.es_principal.is_(True),
            Wallet.estado != EstadoWallet.cerrada,
        )
    )
    if wallet is None:
        wallet = Wallet(
            owner_type=OwnerTypeWallet.organizacion,
            usuario_id=None,
            organizacion_owner_id=organizacion.id,
            organizacion_id=organizacion.id,
        )
        db.add(wallet)

    wallet.alias = alias
    wallet.tipo = TipoWallet.empresa
    wallet.estado = EstadoWallet.activa
    wallet.moneda = MonedaWallet.ARS
    wallet.saldo = saldo
    wallet.limite_operacion = None
    wallet.es_principal = True
    db.flush()
    return wallet


def _ensure_movement(
    db: Session,
    *,
    referencia_externa: str,
    organizacion_id: UUID,
    tipo: TipoMovimiento,
    monto: Decimal,
    descripcion: str,
    wallet_origen_id: UUID | None = None,
    wallet_destino_id: UUID | None = None,
    metadata: dict[str, str] | None = None,
) -> Movimiento:
    movimiento = db.scalar(select(Movimiento).where(Movimiento.referencia_externa == referencia_externa))
    if movimiento is None:
        movimiento = Movimiento(referencia_externa=referencia_externa)
        db.add(movimiento)

    movimiento.organizacion_id = organizacion_id
    movimiento.wallet_origen_id = wallet_origen_id
    movimiento.wallet_destino_id = wallet_destino_id
    movimiento.tipo = tipo
    movimiento.estado = EstadoMovimiento.aprobada
    movimiento.monto = monto
    movimiento.moneda = MonedaWallet.ARS
    movimiento.descripcion = descripcion
    movimiento.metadata_movimiento = metadata or {"seed": "dev_demo"}
    movimiento.es_reversa = False
    movimiento.motivo_reversa = None
    db.flush()
    return movimiento


def _ensure_notification(
    db: Session,
    *,
    organizacion_id: UUID,
    usuario_id: UUID,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    metadata: dict[str, str] | None = None,
) -> Notificacion:
    notification = db.scalar(
        select(Notificacion).where(
            Notificacion.organizacion_id == organizacion_id,
            Notificacion.usuario_id == usuario_id,
            Notificacion.tipo == tipo,
            Notificacion.titulo == titulo,
        )
    )
    if notification is None:
        notification = Notificacion(
            organizacion_id=organizacion_id,
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
        )
        db.add(notification)

    notification.canal = CanalNotificacion.interna
    notification.mensaje = mensaje
    notification.metadata_notificacion = metadata or {"seed": "dev_demo"}
    notification.leida = False
    notification.enviada = True
    notification.error_envio = None
    db.flush()
    return notification


def _hash_api_key(raw_key: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_api_key() -> str:
    return f"wsk_test_{secrets.token_urlsafe(32)}"


def _ensure_demo_api_key(db: Session, *, organizacion: Organizacion) -> tuple[APIKey, str | None]:
    api_key = db.scalar(
        select(APIKey).where(
            APIKey.organizacion_id == organizacion.id,
            APIKey.nombre.in_([DEMO_API_KEY_NAME, "Demo API Key inactiva"]),
        )
    )
    raw_key: str | None = None
    if api_key is None:
        raw_key = _generate_api_key()
        api_key = APIKey(key_prefix=raw_key[:20], key_hash=_hash_api_key(raw_key))
        db.add(api_key)

    api_key.organizacion_id = organizacion.id
    api_key.nombre = DEMO_API_KEY_NAME
    api_key.scopes = DEMO_API_KEY_SCOPES
    api_key.activa = True
    api_key.ultimo_uso_en = None
    db.flush()
    return api_key, raw_key


def _ensure_demo_webhook(db: Session, *, organizacion: Organizacion) -> WebhookEndpoint:
    webhook = db.scalar(
        select(WebhookEndpoint).where(
            WebhookEndpoint.organizacion_id == organizacion.id,
            WebhookEndpoint.nombre.in_([DEMO_WEBHOOK_NAME, "Webhook demo inactivo"]),
        )
    )
    if webhook is None:
        webhook = WebhookEndpoint(
            organizacion_id=organizacion.id,
            nombre=DEMO_WEBHOOK_NAME,
            secret_encrypted=encrypt_webhook_secret(DEMO_WEBHOOK_SECRET),
        )
        db.add(webhook)

    webhook.nombre = DEMO_WEBHOOK_NAME
    webhook.url = "https://example.com/webhook-demo"
    webhook.eventos = [
        "movimiento.creado",
        "pago_organizacion.creado",
        "ecommerce.order_paid",
        "ecommerce.order_processed",
        "ecommerce.order_failed",
        "recompensa.aplicada",
    ]
    webhook.activo = False
    db.flush()
    return webhook


def _ensure_reward_rule(db: Session, *, organizacion: Organizacion) -> ReglaRecompensa:
    regla = db.scalar(
        select(ReglaRecompensa).where(
            ReglaRecompensa.organizacion_id == organizacion.id,
            ReglaRecompensa.nombre == DEMO_REWARD_RULE_NAME,
        )
    )
    if regla is None:
        regla = ReglaRecompensa(organizacion_id=organizacion.id, nombre=DEMO_REWARD_RULE_NAME)
        db.add(regla)

    regla.descripcion = "Regla demo para acreditar cashback interno sobre compras registradas."
    regla.tipo = TipoRecompensa.cashback
    regla.estado = EstadoReglaRecompensa.activa
    regla.porcentaje_cashback = Decimal("10.00")
    regla.monto_fijo = None
    regla.moneda_recompensa = MonedaRecompensa.ARS
    regla.monto_minimo_compra = Decimal("1000.00")
    regla.monto_maximo_recompensa = Decimal("2000.00")
    regla.acumulable = True
    regla.fecha_inicio = None
    regla.fecha_fin = None
    db.flush()
    return regla


def _ensure_reward_application(
    db: Session,
    *,
    organizacion: Organizacion,
    regla: ReglaRecompensa,
    usuario: Usuario,
    wallet: Wallet,
    movimiento: Movimiento,
) -> AplicacionRecompensa:
    aplicacion = db.scalar(
        select(AplicacionRecompensa).where(
            AplicacionRecompensa.organizacion_id == organizacion.id,
            AplicacionRecompensa.referencia_externa == DEMO_REWARD_REFERENCE,
        )
    )
    if aplicacion is None:
        aplicacion = AplicacionRecompensa(
            organizacion_id=organizacion.id,
            referencia_externa=DEMO_REWARD_REFERENCE,
        )
        db.add(aplicacion)

    aplicacion.regla_id = regla.id
    aplicacion.usuario_id = usuario.id
    aplicacion.wallet_destino_id = wallet.id
    aplicacion.movimiento_id = movimiento.id
    aplicacion.monto_compra = Decimal("15000.00")
    aplicacion.monto_recompensa = Decimal("1500.00")
    aplicacion.moneda_recompensa = MonedaRecompensa.ARS
    aplicacion.metadata_aplicacion = {"seed": "dev_demo", "calculo": "min(15000 * 10%, 2000)"}
    db.flush()
    return aplicacion


def seed_demo(db: Session) -> dict[str, str]:
    """Crea o actualiza datos demo locales sin duplicar registros base."""
    organizacion = _ensure_demo_organization(db)
    users = _ensure_demo_users(db, organizacion=organizacion)
    owner = users["owner"]
    admin = users["admin"]
    cliente = users["cliente"]

    owner_wallet = _ensure_user_wallet(
        db,
        organizacion=organizacion,
        usuario=owner,
        alias="Wallet Owner Demo",
        saldo=DEMO_OWNER_BALANCE,
    )
    admin_wallet = _ensure_user_wallet(
        db,
        organizacion=organizacion,
        usuario=admin,
        alias="Wallet Admin Demo",
        saldo=DEMO_ADMIN_BALANCE,
    )
    cliente_wallet = _ensure_user_wallet(
        db,
        organizacion=organizacion,
        usuario=cliente,
        alias="Wallet Cliente Demo",
        saldo=DEMO_CLIENT_BALANCE,
    )
    org_wallet = _ensure_organization_wallet(
        db,
        organizacion=organizacion,
        alias="Wallet Empresa Demo",
        saldo=DEMO_ORG_BALANCE,
    )

    deposito = _ensure_movement(
        db,
        referencia_externa="seed-deposito-cliente",
        organizacion_id=organizacion.id,
        tipo=TipoMovimiento.deposito,
        monto=Decimal("10000.00"),
        descripcion="Deposito inicial demo",
        wallet_destino_id=cliente_wallet.id,
    )
    pago = _ensure_movement(
        db,
        referencia_externa="seed-pago-cliente-organizacion",
        organizacion_id=organizacion.id,
        tipo=TipoMovimiento.pago,
        monto=Decimal("1250.00"),
        descripcion="Pago demo cliente a organizacion",
        wallet_origen_id=cliente_wallet.id,
        wallet_destino_id=org_wallet.id,
        metadata={"seed": "dev_demo", "operacion": "pago_organizacion"},
    )
    cashback = _ensure_movement(
        db,
        referencia_externa="seed-cashback-cliente",
        organizacion_id=organizacion.id,
        tipo=TipoMovimiento.cashback,
        monto=Decimal("250.00"),
        descripcion="Cashback demo cliente",
        wallet_destino_id=cliente_wallet.id,
        metadata={"seed": "dev_demo", "operacion": "cashback"},
    )
    regla_recompensa = _ensure_reward_rule(db, organizacion=organizacion)
    recompensa_movimiento = _ensure_movement(
        db,
        referencia_externa=DEMO_REWARD_REFERENCE,
        organizacion_id=organizacion.id,
        tipo=TipoMovimiento.cashback,
        monto=Decimal("1500.00"),
        descripcion="Recompensa demo por cashback 10%",
        wallet_destino_id=cliente_wallet.id,
        metadata={
            "seed": "dev_demo",
            "operacion": "recompensa",
            "regla_id": str(regla_recompensa.id),
            "monto_compra": "15000.00",
        },
    )
    recompensa_aplicacion = _ensure_reward_application(
        db,
        organizacion=organizacion,
        regla=regla_recompensa,
        usuario=cliente,
        wallet=cliente_wallet,
        movimiento=recompensa_movimiento,
    )
    ajuste = _ensure_movement(
        db,
        referencia_externa="seed-ajuste-organizacion",
        organizacion_id=organizacion.id,
        tipo=TipoMovimiento.ajuste_admin,
        monto=Decimal("5000.00"),
        descripcion="Ajuste admin credito organizacion",
        wallet_destino_id=org_wallet.id,
        metadata={"seed": "dev_demo", "operacion": "credito"},
    )

    _ensure_notification(
        db,
        organizacion_id=organizacion.id,
        usuario_id=owner.id,
        tipo=TipoNotificacion.onboarding_exitoso,
        titulo="Bienvenido a Demo Wallet",
        mensaje="La organizacion demo esta lista para operar con wallets, usuarios e integraciones.",
        metadata={"organizacion_id": str(organizacion.id), "seed": "dev_demo"},
    )
    _ensure_notification(
        db,
        organizacion_id=organizacion.id,
        usuario_id=admin.id,
        tipo=TipoNotificacion.pago_organizacion_recibido,
        titulo="Pago recibido",
        mensaje="La organizacion recibio un pago demo de cliente.",
        metadata={"movimiento_id": str(pago.id), "seed": "dev_demo"},
    )
    _ensure_notification(
        db,
        organizacion_id=organizacion.id,
        usuario_id=users["soporte"].id,
        tipo=TipoNotificacion.seguridad,
        titulo="Revision de integraciones pendiente",
        mensaje="Hay una API Key ecommerce activa y un webhook demo inactivo para revisar en integraciones.",
        metadata={"api_key_scope": ",".join(DEMO_API_KEY_SCOPES), "seed": "dev_demo"},
    )
    _ensure_notification(
        db,
        organizacion_id=organizacion.id,
        usuario_id=cliente.id,
        tipo=TipoNotificacion.movimiento_cashback,
        titulo="Cashback acreditado",
        mensaje="Se acredito un cashback demo en tu wallet.",
        metadata={"movimiento_id": str(cashback.id), "seed": "dev_demo"},
    )
    _ensure_notification(
        db,
        organizacion_id=organizacion.id,
        usuario_id=owner.id,
        tipo=TipoNotificacion.pago_organizacion_recibido,
        titulo="Pago demo recibido",
        mensaje="La organizacion recibio un pago demo.",
        metadata={"movimiento_id": str(pago.id), "seed": "dev_demo"},
    )

    api_key, raw_api_key = _ensure_demo_api_key(db, organizacion=organizacion)
    webhook = _ensure_demo_webhook(db, organizacion=organizacion)

    cliente_wallet.saldo = DEMO_CLIENT_BALANCE
    org_wallet.saldo = DEMO_ORG_BALANCE
    owner_wallet.saldo = DEMO_OWNER_BALANCE
    admin_wallet.saldo = DEMO_ADMIN_BALANCE

    db.commit()
    return {
        "organizacion_id": str(organizacion.id),
        "super_admin_id": str(users["super_admin"].id),
        "owner_id": str(users["owner"].id),
        "admin_id": str(users["admin"].id),
        "soporte_id": str(users["soporte"].id),
        "cliente_id": str(users["cliente"].id),
        "owner_wallet_id": str(owner_wallet.id),
        "admin_wallet_id": str(admin_wallet.id),
        "wallet_cliente_id": str(cliente_wallet.id),
        "wallet_empresa_id": str(org_wallet.id),
        "api_key_demo_id": str(api_key.id),
        "api_key_prefix": api_key.key_prefix,
        "api_key_raw": raw_api_key or "",
        "webhook_demo_id": str(webhook.id),
        "deposito_id": str(deposito.id),
        "pago_id": str(pago.id),
        "cashback_id": str(cashback.id),
        "regla_recompensa_id": str(regla_recompensa.id),
        "aplicacion_recompensa_id": str(recompensa_aplicacion.id),
        "ajuste_id": str(ajuste.id),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos demo locales para Wallet SaaS.")
    parser.add_argument(
        "--allow-unsafe-database",
        action="store_true",
        help="Permite correr en desarrollo si DATABASE_URL no parece wallet_saas local. No saltea validaciones de production.",
    )
    args = parser.parse_args()

    _ensure_dev_database_safety(allow_unsafe_database=args.allow_unsafe_database)
    with SessionLocal() as db:
        summary = seed_demo(db)

    print("Seed demo listo.")
    print(f"Organizacion: {DEMO_ORG['nombre']} ({DEMO_ORG['slug']})")
    print("Credenciales demo:")
    for user_data in DEMO_USERS.values():
        print(f"- {user_data['email']} / {DEMO_PASSWORD}")
    print("URLs:")
    print("- Backend: http://127.0.0.1:8000/docs")
    print("- Frontend: http://127.0.0.1:5173")
    print("IDs principales:")
    print(f"- organizacion: {summary['organizacion_id']}")
    print(f"- super admin: {summary['super_admin_id']}")
    print(f"- owner: {summary['owner_id']}")
    print(f"- admin: {summary['admin_id']}")
    print(f"- soporte: {summary['soporte_id']}")
    print(f"- cliente: {summary['cliente_id']}")
    print(f"- wallet empresa: {summary['wallet_empresa_id']}")
    print(f"- wallet cliente: {summary['wallet_cliente_id']}")
    print(f"- wallet owner: {summary['owner_wallet_id']}")
    print(f"- wallet admin: {summary['admin_wallet_id']}")
    print("Integraciones demo:")
    print(f"- API Key ecommerce activa: {summary['api_key_demo_id']} ({summary['api_key_prefix']})")
    if summary["api_key_raw"]:
        print(f"- API Key real creada por primera vez: {summary['api_key_raw']}")
    else:
        print("- API Key real: no se vuelve a mostrar porque ya existia.")
    print(f"- Webhook inactivo: {summary['webhook_demo_id']}")
    print(f"- Regla recompensa: {summary['regla_recompensa_id']}")
    print(f"- Aplicacion recompensa: {summary['aplicacion_recompensa_id']}")


if __name__ == "__main__":
    main()
