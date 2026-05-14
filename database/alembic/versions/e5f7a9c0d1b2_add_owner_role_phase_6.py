"""add owner role phase 6

Revision ID: e5f7a9c0d1b2
Revises: d4e6f8a1b2c3
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e5f7a9c0d1b2"
down_revision: Union[str, Sequence[str], None] = "d4e6f8a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega owner al enum historico de roles sin cambios destructivos."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE rolusuario ADD VALUE IF NOT EXISTS 'owner'")


def downgrade() -> None:
    """PostgreSQL no permite remover valores de enum de forma segura."""
    pass

