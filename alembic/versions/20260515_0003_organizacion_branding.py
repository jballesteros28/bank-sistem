"""organizacion_branding

Revision ID: 20260515_0003
Revises: 20260515_0002
Create Date: 2026-05-15 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260515_0003"
down_revision: Union[str, None] = "20260515_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizaciones", sa.Column("nombre_comercial", sa.String(length=150), nullable=True))
    op.add_column("organizaciones", sa.Column("logo_url", sa.String(length=500), nullable=True))
    op.add_column("organizaciones", sa.Column("color_primario", sa.String(length=7), nullable=True))
    op.add_column("organizaciones", sa.Column("color_secundario", sa.String(length=7), nullable=True))
    op.add_column("organizaciones", sa.Column("subdominio", sa.String(length=120), nullable=True))
    op.add_column("organizaciones", sa.Column("dominio_personalizado", sa.String(length=255), nullable=True))
    op.add_column(
        "organizaciones",
        sa.Column("moneda_default", sa.String(length=20), server_default="ARS", nullable=False),
    )
    op.add_column(
        "organizaciones",
        sa.Column(
            "timezone",
            sa.String(length=80),
            server_default="America/Argentina/Buenos_Aires",
            nullable=False,
        ),
    )
    op.add_column(
        "organizaciones",
        sa.Column("permite_white_label_activo", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_organizaciones_subdominio", "organizaciones", ["subdominio"], unique=True)
    op.create_index(
        "ix_organizaciones_dominio_personalizado",
        "organizaciones",
        ["dominio_personalizado"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_organizaciones_dominio_personalizado", table_name="organizaciones")
    op.drop_index("ix_organizaciones_subdominio", table_name="organizaciones")
    op.drop_column("organizaciones", "permite_white_label_activo")
    op.drop_column("organizaciones", "timezone")
    op.drop_column("organizaciones", "moneda_default")
    op.drop_column("organizaciones", "dominio_personalizado")
    op.drop_column("organizaciones", "subdominio")
    op.drop_column("organizaciones", "color_secundario")
    op.drop_column("organizaciones", "color_primario")
    op.drop_column("organizaciones", "logo_url")
    op.drop_column("organizaciones", "nombre_comercial")
