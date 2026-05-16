"""initial_wallet_saas_schema

Revision ID: 20260515_0001
Revises:
Create Date: 2026-05-15 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260515_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


uuid_pk = postgresql.UUID(as_uuid=True)

rol_usuario = postgresql.ENUM(
    "cliente", "admin", "owner", "soporte", "super_admin", name="rol_usuario", create_type=False
)
estado_organizacion = postgresql.ENUM(
    "activa", "inactiva", "suspendida", name="estado_organizacion", create_type=False
)
tipo_wallet = postgresql.ENUM(
    "principal",
    "ahorro",
    "empresa",
    "operativa",
    "caja",
    "recompensas",
    name="tipo_wallet",
    create_type=False,
)
owner_type_wallet = postgresql.ENUM("usuario", "organizacion", name="owner_type_wallet", create_type=False)
estado_wallet = postgresql.ENUM(
    "activa", "inactiva", "congelada", "cerrada", name="estado_wallet", create_type=False
)
moneda_wallet = postgresql.ENUM("ARS", "USD", "PUNTOS", name="moneda_wallet", create_type=False)
tipo_movimiento = postgresql.ENUM(
    "deposito",
    "retiro",
    "transferencia",
    "pago",
    "cashback",
    "ajuste_admin",
    "reversa",
    name="tipo_movimiento",
    create_type=False,
)
estado_movimiento = postgresql.ENUM(
    "aprobada", "pendiente", "rechazada", "cancelada", "revertida", name="estado_movimiento", create_type=False
)
tipo_notificacion = postgresql.ENUM(
    "onboarding_exitoso",
    "wallet_creada",
    "movimiento_deposito",
    "movimiento_retiro",
    "movimiento_transferencia",
    "movimiento_pago",
    "movimiento_cashback",
    "movimiento_ajuste_admin",
    "movimiento_reversa",
    "wallet_congelada",
    "wallet_organizacion_creada",
    "pago_organizacion_realizado",
    "pago_organizacion_recibido",
    "organizacion_suspendida",
    "seguridad",
    name="tipo_notificacion",
    create_type=False,
)
canal_notificacion = postgresql.ENUM("interna", "email", name="canal_notificacion", create_type=False)


def _uuid_id_column() -> sa.Column:
    return sa.Column("id", uuid_pk, server_default=sa.text("gen_random_uuid()"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    rol_usuario.create(bind, checkfirst=True)
    estado_organizacion.create(bind, checkfirst=True)
    tipo_wallet.create(bind, checkfirst=True)
    owner_type_wallet.create(bind, checkfirst=True)
    estado_wallet.create(bind, checkfirst=True)
    moneda_wallet.create(bind, checkfirst=True)
    tipo_movimiento.create(bind, checkfirst=True)
    estado_movimiento.create(bind, checkfirst=True)
    tipo_notificacion.create(bind, checkfirst=True)
    canal_notificacion.create(bind, checkfirst=True)

    op.create_table(
        "planes",
        _uuid_id_column(),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio_mensual", sa.Numeric(18, 2), nullable=False),
        sa.Column("limite_usuarios", sa.Integer(), nullable=True),
        sa.Column("limite_wallets", sa.Integer(), nullable=True),
        sa.Column("limite_movimientos_mes", sa.Integer(), nullable=True),
        sa.Column("permite_webhooks", sa.Boolean(), nullable=False),
        sa.Column("permite_white_label", sa.Boolean(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_planes_codigo", "planes", ["codigo"], unique=True)
    op.create_index("ix_planes_nombre", "planes", ["nombre"], unique=True)

    op.create_table(
        "organizaciones",
        _uuid_id_column(),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("email_contacto", sa.String(length=255), nullable=False),
        sa.Column("nombre_comercial", sa.String(length=150), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("color_primario", sa.String(length=7), nullable=True),
        sa.Column("color_secundario", sa.String(length=7), nullable=True),
        sa.Column("subdominio", sa.String(length=120), nullable=True),
        sa.Column("dominio_personalizado", sa.String(length=255), nullable=True),
        sa.Column("moneda_default", sa.String(length=20), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("permite_white_label_activo", sa.Boolean(), nullable=False),
        sa.Column("plan_id", uuid_pk, nullable=True),
        sa.Column("estado", estado_organizacion, nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["planes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizaciones_subdominio", "organizaciones", ["subdominio"], unique=True)
    op.create_index(
        "ix_organizaciones_dominio_personalizado",
        "organizaciones",
        ["dominio_personalizado"],
        unique=True,
    )

    op.create_table(
        "usuarios",
        _uuid_id_column(),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("es_activo", sa.Boolean(), nullable=False),
        sa.Column("rol", rol_usuario, nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organizacion_id", uuid_pk, nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"], unique=False)
    op.create_index("ix_usuarios_organizacion_id", "usuarios", ["organizacion_id"], unique=False)

    op.create_table(
        "wallets",
        _uuid_id_column(),
        sa.Column("alias", sa.String(length=80), nullable=True),
        sa.Column("tipo", tipo_wallet, nullable=False),
        sa.Column("estado", estado_wallet, nullable=False),
        sa.Column("moneda", moneda_wallet, nullable=False),
        sa.Column("saldo", sa.Numeric(18, 2), nullable=False),
        sa.Column("limite_operacion", sa.Numeric(18, 2), nullable=True),
        sa.Column("es_principal", sa.Boolean(), nullable=False),
        sa.Column("owner_type", owner_type_wallet, nullable=False),
        sa.Column("usuario_id", uuid_pk, nullable=True),
        sa.Column("organizacion_owner_id", uuid_pk, nullable=True),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "("
            "owner_type = 'usuario' AND usuario_id IS NOT NULL AND organizacion_owner_id IS NULL"
            ") OR ("
            "owner_type = 'organizacion' AND organizacion_owner_id IS NOT NULL AND usuario_id IS NULL"
            ")",
            name="ck_wallet_owner_consistency",
        ),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organizacion_owner_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallets_id", "wallets", ["id"], unique=False)
    op.create_index("ix_wallets_organizacion_id", "wallets", ["organizacion_id"], unique=False)

    op.create_table(
        "movimientos",
        _uuid_id_column(),
        sa.Column("wallet_origen_id", uuid_pk, nullable=True),
        sa.Column("wallet_destino_id", uuid_pk, nullable=True),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("moneda", moneda_wallet, nullable=False),
        sa.Column("tipo", tipo_movimiento, nullable=False),
        sa.Column("estado", estado_movimiento, nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("referencia_externa", sa.String(length=120), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("movimiento_origen_id", uuid_pk, nullable=True),
        sa.Column("es_reversa", sa.Boolean(), nullable=False),
        sa.Column("motivo_reversa", sa.String(length=255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["movimiento_origen_id"], ["movimientos.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["wallet_destino_id"], ["wallets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["wallet_origen_id"], ["wallets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movimientos_id", "movimientos", ["id"], unique=False)
    op.create_index("ix_movimientos_movimiento_origen_id", "movimientos", ["movimiento_origen_id"], unique=False)
    op.create_index("ix_movimientos_organizacion_id", "movimientos", ["organizacion_id"], unique=False)
    op.create_index("ix_movimientos_referencia_externa", "movimientos", ["referencia_externa"], unique=False)
    op.create_index("ix_movimientos_wallet_destino_id", "movimientos", ["wallet_destino_id"], unique=False)
    op.create_index("ix_movimientos_wallet_origen_id", "movimientos", ["wallet_origen_id"], unique=False)

    op.create_table(
        "api_keys",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("ultimo_uso_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_revocacion", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_prefix"),
    )
    op.create_index("ix_api_keys_id", "api_keys", ["id"], unique=False)
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"], unique=True)
    op.create_index("ix_api_keys_organizacion_id", "api_keys", ["organizacion_id"], unique=False)

    op.create_table(
        "webhook_endpoints",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("eventos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("secret_encrypted", sa.String(length=1000), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_endpoints_id", "webhook_endpoints", ["id"], unique=False)
    op.create_index("ix_webhook_endpoints_organizacion_id", "webhook_endpoints", ["organizacion_id"], unique=False)

    op.create_table(
        "webhook_deliveries",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("webhook_endpoint_id", uuid_pk, nullable=False),
        sa.Column("evento", sa.String(length=120), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("respuesta_body", sa.Text(), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_ultimo_intento", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["webhook_endpoint_id"], ["webhook_endpoints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_deliveries_evento", "webhook_deliveries", ["evento"], unique=False)
    op.create_index("ix_webhook_deliveries_id", "webhook_deliveries", ["id"], unique=False)
    op.create_index("ix_webhook_deliveries_organizacion_id", "webhook_deliveries", ["organizacion_id"], unique=False)
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"], unique=False)
    op.create_index(
        "ix_webhook_deliveries_webhook_endpoint_id",
        "webhook_deliveries",
        ["webhook_endpoint_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        _uuid_id_column(),
        sa.Column("evento", sa.String(length=120), nullable=False),
        sa.Column("mensaje", sa.String(length=500), nullable=False),
        sa.Column("nivel", sa.String(length=20), nullable=False),
        sa.Column("actor_usuario_id", uuid_pk, nullable=True),
        sa.Column("organizacion_id", uuid_pk, nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=80), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_evento", "audit_logs", ["evento"], unique=False)
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"], unique=False)
    op.create_index("ix_audit_logs_organizacion_id", "audit_logs", ["organizacion_id"], unique=False)

    op.create_table(
        "notificaciones",
        _uuid_id_column(),
        sa.Column("usuario_id", uuid_pk, nullable=True),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("tipo", tipo_notificacion, nullable=False),
        sa.Column("canal", canal_notificacion, nullable=False),
        sa.Column("titulo", sa.String(length=180), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("leida", sa.Boolean(), nullable=False),
        sa.Column("enviada", sa.Boolean(), nullable=False),
        sa.Column("error_envio", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_lectura", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_envio", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notificaciones_id", "notificaciones", ["id"], unique=False)
    op.create_index("ix_notificaciones_organizacion_id", "notificaciones", ["organizacion_id"], unique=False)
    op.create_index("ix_notificaciones_usuario_id", "notificaciones", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_table("notificaciones")
    op.drop_table("audit_logs")
    op.execute("DROP TABLE IF EXISTS webhook_deliveries")
    op.execute("DROP TABLE IF EXISTS webhook_endpoints")
    op.execute("DROP TABLE IF EXISTS api_keys")
    op.drop_table("movimientos")
    op.drop_table("wallets")
    op.drop_table("usuarios")
    op.drop_table("organizaciones")
    op.drop_table("planes")

    bind = op.get_bind()
    canal_notificacion.drop(bind, checkfirst=True)
    tipo_notificacion.drop(bind, checkfirst=True)
    estado_movimiento.drop(bind, checkfirst=True)
    tipo_movimiento.drop(bind, checkfirst=True)
    moneda_wallet.drop(bind, checkfirst=True)
    estado_wallet.drop(bind, checkfirst=True)
    owner_type_wallet.drop(bind, checkfirst=True)
    tipo_wallet.drop(bind, checkfirst=True)
    estado_organizacion.drop(bind, checkfirst=True)
    rol_usuario.drop(bind, checkfirst=True)
