"""recompensas_store_credit

Revision ID: 20260517_0002
Revises: 20260515_0001
Create Date: 2026-05-17 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260517_0002"
down_revision: Union[str, None] = "20260515_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


uuid_pk = postgresql.UUID(as_uuid=True)

tipo_recompensa = postgresql.ENUM(
    "cashback",
    "puntos",
    "credito_tienda",
    name="tipo_recompensa",
    create_type=False,
)
estado_regla_recompensa = postgresql.ENUM(
    "activa",
    "inactiva",
    "pausada",
    name="estado_regla_recompensa",
    create_type=False,
)
moneda_recompensa = postgresql.ENUM("ARS", "USD", "PUNTOS", name="moneda_recompensa", create_type=False)


def _uuid_id_column() -> sa.Column:
    return sa.Column("id", uuid_pk, server_default=sa.text("gen_random_uuid()"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("ALTER TYPE tipo_movimiento ADD VALUE IF NOT EXISTS 'credito_tienda'")
    op.execute("ALTER TYPE tipo_notificacion ADD VALUE IF NOT EXISTS 'recompensa_aplicada'")
    tipo_recompensa.create(bind, checkfirst=True)
    estado_regla_recompensa.create(bind, checkfirst=True)
    moneda_recompensa.create(bind, checkfirst=True)

    op.create_table(
        "reglas_recompensa",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=True),
        sa.Column("tipo", tipo_recompensa, nullable=False),
        sa.Column("estado", estado_regla_recompensa, nullable=False),
        sa.Column("porcentaje_cashback", sa.Numeric(5, 2), nullable=True),
        sa.Column("monto_fijo", sa.Numeric(18, 2), nullable=True),
        sa.Column("moneda_recompensa", moneda_recompensa, nullable=False),
        sa.Column("monto_minimo_compra", sa.Numeric(18, 2), nullable=True),
        sa.Column("monto_maximo_recompensa", sa.Numeric(18, 2), nullable=True),
        sa.Column("acumulable", sa.Boolean(), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reglas_recompensa_id", "reglas_recompensa", ["id"], unique=False)
    op.create_index("ix_reglas_recompensa_organizacion_id", "reglas_recompensa", ["organizacion_id"], unique=False)

    op.create_table(
        "aplicaciones_recompensa",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("regla_id", uuid_pk, nullable=False),
        sa.Column("usuario_id", uuid_pk, nullable=False),
        sa.Column("wallet_destino_id", uuid_pk, nullable=False),
        sa.Column("movimiento_id", uuid_pk, nullable=True),
        sa.Column("monto_compra", sa.Numeric(18, 2), nullable=False),
        sa.Column("monto_recompensa", sa.Numeric(18, 2), nullable=False),
        sa.Column("moneda_recompensa", moneda_recompensa, nullable=False),
        sa.Column("referencia_externa", sa.String(length=120), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["movimiento_id"], ["movimientos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["regla_id"], ["reglas_recompensa.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["wallet_destino_id"], ["wallets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aplicaciones_recompensa_id", "aplicaciones_recompensa", ["id"], unique=False)
    op.create_index(
        "ix_aplicaciones_recompensa_movimiento_id",
        "aplicaciones_recompensa",
        ["movimiento_id"],
        unique=False,
    )
    op.create_index(
        "ix_aplicaciones_recompensa_organizacion_id",
        "aplicaciones_recompensa",
        ["organizacion_id"],
        unique=False,
    )
    op.create_index("ix_aplicaciones_recompensa_referencia_externa", "aplicaciones_recompensa", ["referencia_externa"])
    op.create_index("ix_aplicaciones_recompensa_regla_id", "aplicaciones_recompensa", ["regla_id"], unique=False)
    op.create_index("ix_aplicaciones_recompensa_usuario_id", "aplicaciones_recompensa", ["usuario_id"], unique=False)
    op.create_index(
        "ix_aplicaciones_recompensa_wallet_destino_id",
        "aplicaciones_recompensa",
        ["wallet_destino_id"],
        unique=False,
    )
    op.create_index(
        "uq_aplicaciones_recompensa_org_referencia",
        "aplicaciones_recompensa",
        ["organizacion_id", "referencia_externa"],
        unique=True,
        postgresql_where=sa.text("referencia_externa IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("aplicaciones_recompensa")
    op.drop_table("reglas_recompensa")

    bind = op.get_bind()
    moneda_recompensa.drop(bind, checkfirst=True)
    estado_regla_recompensa.drop(bind, checkfirst=True)
    tipo_recompensa.drop(bind, checkfirst=True)
