"""planes_saas

Revision ID: 20260515_0002
Revises: 20260514_0001
Create Date: 2026-05-15 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260515_0002"
down_revision: Union[str, None] = "20260514_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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

    op.add_column("organizaciones", sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_organizaciones_plan_id_planes",
        "organizaciones",
        "planes",
        ["plan_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_organizaciones_plan_id_planes", "organizaciones", type_="foreignkey")
    op.drop_column("organizaciones", "plan_id")
    op.drop_index("ix_planes_nombre", table_name="planes")
    op.drop_index("ix_planes_codigo", table_name="planes")
    op.drop_table("planes")
