"""ecommerce_integrations

Revision ID: 20260517_0003
Revises: 20260517_0002
Create Date: 2026-05-17 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260517_0003"
down_revision: Union[str, None] = "20260517_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


uuid_pk = postgresql.UUID(as_uuid=True)


def _uuid_id_column() -> sa.Column:
    return sa.Column("id", uuid_pk, server_default=sa.text("gen_random_uuid()"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "ecommerce_order_events",
        _uuid_id_column(),
        sa.Column("organizacion_id", uuid_pk, nullable=False),
        sa.Column("proveedor", sa.String(length=60), nullable=False),
        sa.Column("external_order_id", sa.String(length=160), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("procesado", sa.Boolean(), nullable=False),
        sa.Column("recompensa_aplicada_id", uuid_pk, nullable=True),
        sa.Column("error_procesamiento", sa.String(length=500), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_procesamiento", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_ecommerce_order_events_amount_positive"),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recompensa_aplicada_id"], ["aplicaciones_recompensa.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ecommerce_order_events_id", "ecommerce_order_events", ["id"], unique=False)
    op.create_index(
        "ix_ecommerce_order_events_organizacion_id",
        "ecommerce_order_events",
        ["organizacion_id"],
        unique=False,
    )
    op.create_index(
        "ix_ecommerce_order_events_customer_email",
        "ecommerce_order_events",
        ["customer_email"],
        unique=False,
    )
    op.create_index("ix_ecommerce_order_events_status", "ecommerce_order_events", ["status"], unique=False)
    op.create_index("ix_ecommerce_order_events_procesado", "ecommerce_order_events", ["procesado"], unique=False)
    op.create_index(
        "ix_ecommerce_order_events_recompensa_aplicada_id",
        "ecommerce_order_events",
        ["recompensa_aplicada_id"],
        unique=False,
    )
    op.create_index(
        "uq_ecommerce_order_events_org_provider_order",
        "ecommerce_order_events",
        ["organizacion_id", "proveedor", "external_order_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("ecommerce_order_events")
