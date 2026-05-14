"""movimientos wallet saas phase 4

Revision ID: d4e6f8a1b2c3
Revises: c7f3a8b2d4e5
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e6f8a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7f3a8b2d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega el dominio Movimiento sin renombrar ni destruir transacciones."""
    bind = op.get_bind()

    tipo_movimiento_enum = postgresql.ENUM(
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
    estado_movimiento_enum = postgresql.ENUM(
        "pendiente",
        "aprobada",
        "rechazada",
        "cancelada",
        "revertida",
        name="estado_movimiento",
        create_type=False,
    )
    tipo_movimiento_enum.create(bind, checkfirst=True)
    estado_movimiento_enum.create(bind, checkfirst=True)

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipotransaccion ADD VALUE IF NOT EXISTS 'pago'")
        op.execute("ALTER TYPE tipotransaccion ADD VALUE IF NOT EXISTS 'cashback'")
        op.execute("ALTER TYPE tipotransaccion ADD VALUE IF NOT EXISTS 'ajuste_admin'")
        op.execute("ALTER TYPE tipotransaccion ADD VALUE IF NOT EXISTS 'reversa'")
        op.execute("ALTER TYPE estadotransaccion ADD VALUE IF NOT EXISTS 'aprobada'")
        op.execute("ALTER TYPE estadotransaccion ADD VALUE IF NOT EXISTS 'rechazada'")
        op.execute("ALTER TYPE estadotransaccion ADD VALUE IF NOT EXISTS 'cancelada'")
        op.execute("ALTER TYPE estadotransaccion ADD VALUE IF NOT EXISTS 'revertida'")

    op.add_column("transacciones", sa.Column("referencia_externa", sa.String(length=120), nullable=True))
    op.add_column("transacciones", sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("transacciones", sa.Column("movimiento_origen_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "transacciones",
        sa.Column(
            "es_reversa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )
    op.add_column("transacciones", sa.Column("motivo_reversa", sa.String(length=255), nullable=True))

    op.create_index("ix_transacciones_referencia_externa", "transacciones", ["referencia_externa"], unique=False)
    op.create_index("ix_transacciones_movimiento_origen_id", "transacciones", ["movimiento_origen_id"], unique=False)


def downgrade() -> None:
    """Revierte columnas nuevas; los valores agregados a enums historicos permanecen."""
    op.drop_index("ix_transacciones_movimiento_origen_id", table_name="transacciones")
    op.drop_index("ix_transacciones_referencia_externa", table_name="transacciones")
    op.drop_column("transacciones", "motivo_reversa")
    op.drop_column("transacciones", "es_reversa")
    op.drop_column("transacciones", "movimiento_origen_id")
    op.drop_column("transacciones", "metadata")
    op.drop_column("transacciones", "referencia_externa")

    op.execute("DROP TYPE IF EXISTS estado_movimiento;")
    op.execute("DROP TYPE IF EXISTS tipo_movimiento;")

