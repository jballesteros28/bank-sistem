"""add super admin role and demo email

Revision ID: b6e1c2f4a9d3
Revises: 8c1f4e2d9a10
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b6e1c2f4a9d3"
down_revision: Union[str, Sequence[str], None] = "8c1f4e2d9a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade no destructivo para preparar el rol global SaaS."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE rolusuario ADD VALUE IF NOT EXISTS 'super_admin'")
    op.execute(
        """
        UPDATE organizaciones
        SET email_contacto = 'demo@example.com'
        WHERE slug = 'organizacion-demo'
        """
    )


def downgrade() -> None:
    """PostgreSQL no permite remover valores de enum de forma segura."""
    op.execute(
        """
        UPDATE organizaciones
        SET email_contacto = 'demo@example.com'
        WHERE slug = 'organizacion-demo'
        """
    )
