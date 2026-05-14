"""add organizaciones phase 1

Revision ID: 8c1f4e2d9a10
Revises: 35acd8253051
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8c1f4e2d9a10"
down_revision: Union[str, Sequence[str], None] = "35acd8253051"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEMO_ORGANIZACION_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    """Upgrade schema sin cambios destructivos."""
    bind = op.get_bind()

    estado_organizacion_enum = postgresql.ENUM(
        "activa",
        "inactiva",
        "suspendida",
        name="estado_organizacion",
        create_type=False,
    )
    estado_organizacion_enum.create(bind, checkfirst=True)

    op.create_table(
        "organizaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("email_contacto", sa.String(), nullable=False),
        sa.Column(
            "estado",
            estado_organizacion_enum,
            nullable=False,
            server_default="activa",
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizaciones_slug", "organizaciones", ["slug"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO organizaciones (id, nombre, slug, email_contacto, estado, fecha_creacion)
            VALUES (
                :id,
                'Organización Demo',
                'organizacion-demo',
                'demo@wallet.local',
                'activa',
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (slug) DO NOTHING
            """
        ).bindparams(id=DEMO_ORGANIZACION_ID)
    )

    op.add_column(
        "usuarios",
        sa.Column("organizacion_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "cuentas",
        sa.Column("organizacion_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "transacciones",
        sa.Column("organizacion_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_usuarios_organizacion_id_organizaciones",
        "usuarios",
        "organizaciones",
        ["organizacion_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_cuentas_organizacion_id_organizaciones",
        "cuentas",
        "organizaciones",
        ["organizacion_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_transacciones_organizacion_id_organizaciones",
        "transacciones",
        "organizaciones",
        ["organizacion_id"],
        ["id"],
    )

    op.create_index("ix_usuarios_organizacion_id", "usuarios", ["organizacion_id"], unique=False)
    op.create_index("ix_cuentas_organizacion_id", "cuentas", ["organizacion_id"], unique=False)
    op.create_index(
        "ix_transacciones_organizacion_id",
        "transacciones",
        ["organizacion_id"],
        unique=False,
    )

    # Datos heredados: asociar todo al tenant demo sin exigir NOT NULL todavia.
    op.execute(
        sa.text(
            """
            UPDATE usuarios
            SET organizacion_id = :id
            WHERE organizacion_id IS NULL
            """
        ).bindparams(id=DEMO_ORGANIZACION_ID)
    )
    op.execute(
        """
        UPDATE cuentas
        SET organizacion_id = usuarios.organizacion_id
        FROM usuarios
        WHERE cuentas.usuario_id = usuarios.id
          AND cuentas.organizacion_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE transacciones
        SET organizacion_id = cuentas.organizacion_id
        FROM cuentas
        WHERE transacciones.cuenta_origen_id = cuentas.id
          AND transacciones.organizacion_id IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_transacciones_organizacion_id", table_name="transacciones")
    op.drop_index("ix_cuentas_organizacion_id", table_name="cuentas")
    op.drop_index("ix_usuarios_organizacion_id", table_name="usuarios")

    op.drop_constraint(
        "fk_transacciones_organizacion_id_organizaciones",
        "transacciones",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cuentas_organizacion_id_organizaciones",
        "cuentas",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_usuarios_organizacion_id_organizaciones",
        "usuarios",
        type_="foreignkey",
    )

    op.drop_column("transacciones", "organizacion_id")
    op.drop_column("cuentas", "organizacion_id")
    op.drop_column("usuarios", "organizacion_id")

    op.drop_index("ix_organizaciones_slug", table_name="organizaciones")
    op.drop_table("organizaciones")
    op.execute("DROP TYPE IF EXISTS estado_organizacion;")
