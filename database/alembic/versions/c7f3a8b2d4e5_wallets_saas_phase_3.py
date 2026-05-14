"""wallets saas phase 3

Revision ID: c7f3a8b2d4e5
Revises: b6e1c2f4a9d3
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c7f3a8b2d4e5"
down_revision: Union[str, Sequence[str], None] = "b6e1c2f4a9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega soporte wallet sin modificar ni eliminar la tabla cuentas."""
    bind = op.get_bind()

    tipo_wallet_enum = postgresql.ENUM(
        "principal",
        "ahorro",
        "recompensas",
        "empresa",
        name="tipo_wallet",
        create_type=False,
    )
    estado_wallet_enum = postgresql.ENUM(
        "activa",
        "inactiva",
        "congelada",
        "cerrada",
        name="estado_wallet",
        create_type=False,
    )
    moneda_wallet_enum = postgresql.ENUM(
        "ARS",
        "USD",
        "USDT",
        "PUNTOS",
        name="moneda_wallet",
        create_type=False,
    )

    tipo_wallet_enum.create(bind, checkfirst=True)
    estado_wallet_enum.create(bind, checkfirst=True)
    moneda_wallet_enum.create(bind, checkfirst=True)

    # Los campos historicos tipo/estado se conservan; solo se amplian para poder
    # guardar wallets nuevas en la misma tabla sin romper /cuentas.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipocuenta ADD VALUE IF NOT EXISTS 'principal'")
        op.execute("ALTER TYPE tipocuenta ADD VALUE IF NOT EXISTS 'recompensas'")
        op.execute("ALTER TYPE tipocuenta ADD VALUE IF NOT EXISTS 'empresa'")
        op.execute("ALTER TYPE estadocuenta ADD VALUE IF NOT EXISTS 'cerrada'")

    op.add_column("cuentas", sa.Column("alias", sa.String(length=80), nullable=True))
    op.add_column(
        "cuentas",
        sa.Column(
            "moneda",
            moneda_wallet_enum,
            nullable=False,
            server_default="ARS",
        ),
    )
    op.add_column(
        "cuentas",
        sa.Column("limite_operacion", sa.NUMERIC(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "cuentas",
        sa.Column(
            "es_principal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )
    op.add_column(
        "cuentas",
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_index(
        "ux_cuentas_wallet_principal_por_usuario_org",
        "cuentas",
        ["usuario_id", "organizacion_id"],
        unique=True,
        postgresql_where=sa.text("es_principal = true AND estado <> 'cerrada'"),
    )


def downgrade() -> None:
    """Revierte solo columnas e indices agregados; no remueve valores de enums."""
    op.drop_index("ux_cuentas_wallet_principal_por_usuario_org", table_name="cuentas")
    op.drop_column("cuentas", "fecha_creacion")
    op.drop_column("cuentas", "es_principal")
    op.drop_column("cuentas", "limite_operacion")
    op.drop_column("cuentas", "moneda")
    op.drop_column("cuentas", "alias")

    op.execute("DROP TYPE IF EXISTS moneda_wallet;")
    op.execute("DROP TYPE IF EXISTS estado_wallet;")
    op.execute("DROP TYPE IF EXISTS tipo_wallet;")

