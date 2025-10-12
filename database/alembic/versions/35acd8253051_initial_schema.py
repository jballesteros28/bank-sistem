"""initial schema

Revision ID: 35acd8253051
Revises: 
Create Date: 2025-09-29 15:21:05.659751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '35acd8253051'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema con enums explícitos."""

    # Crear enums explícitamente
    rol_enum = postgresql.ENUM('cliente', 'admin', 'soporte', name='rolusuario')
    tipo_cuenta_enum = postgresql.ENUM('ahorro', 'corriente', 'sueldo', name='tipocuenta')
    estado_cuenta_enum = postgresql.ENUM('activa', 'inactiva', 'congelada', name='estadocuenta')
    tipo_transaccion_enum = postgresql.ENUM('transferencia', 'deposito', 'retiro', name='tipotransaccion')
    estado_transaccion_enum = postgresql.ENUM('completada', 'fallida', 'pendiente', name='estadotransaccion')

    rol_enum.create(op.get_bind(), checkfirst=True)
    tipo_cuenta_enum.create(op.get_bind(), checkfirst=True)
    estado_cuenta_enum.create(op.get_bind(), checkfirst=True)
    tipo_transaccion_enum.create(op.get_bind(), checkfirst=True)
    estado_transaccion_enum.create(op.get_bind(), checkfirst=True)

    # Tabla usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('es_activo', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('rol', rol_enum, nullable=False, server_default='cliente'),
        sa.Column('intentos_fallidos', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('bloqueado_hasta', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)

    # Tabla cuentas
    op.create_table(
        'cuentas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.String(), nullable=False),
        sa.Column('tipo', tipo_cuenta_enum, nullable=False),
        sa.Column('saldo', sa.NUMERIC(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column('estado', estado_cuenta_enum, nullable=False, server_default="activa"),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cuentas_id'), 'cuentas', ['id'], unique=False)
    op.create_index(op.f('ix_cuentas_numero'), 'cuentas', ['numero'], unique=True)

    # Tabla transacciones
    op.create_table(
        'transacciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuenta_origen_id', sa.Integer(), nullable=False),
        sa.Column('cuenta_destino_id', sa.Integer(), nullable=False),
        sa.Column('monto', sa.NUMERIC(precision=12, scale=2), nullable=False),
        sa.Column('tipo', tipo_transaccion_enum, nullable=False),
        sa.Column('fecha', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('estado', estado_transaccion_enum, nullable=False, server_default="pendiente"),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['cuenta_destino_id'], ['cuentas.id']),
        sa.ForeignKeyConstraint(['cuenta_origen_id'], ['cuentas.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transacciones_id'), 'transacciones', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f('ix_transacciones_id'), table_name='transacciones')
    op.drop_table('transacciones')
    op.drop_index(op.f('ix_cuentas_numero'), table_name='cuentas')
    op.drop_index(op.f('ix_cuentas_id'), table_name='cuentas')
    op.drop_table('cuentas')
    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_table('usuarios')

    # Borrar enums explícitamente
    op.execute("DROP TYPE IF EXISTS rolusuario CASCADE;")
    op.execute("DROP TYPE IF EXISTS tipocuenta CASCADE;")
    op.execute("DROP TYPE IF EXISTS estadocuenta CASCADE;")
    op.execute("DROP TYPE IF EXISTS tipotransaccion CASCADE;")
    op.execute("DROP TYPE IF EXISTS estadotransaccion CASCADE;")