# ─────────────────────────────────────────────────────────────────────────────
# Importaciones necesarias
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import uuid

from sqlalchemy import NUMERIC, ForeignKey, String
# Tipos de columnas de SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM as PgEnum  # ENUM nativo de PostgreSQL
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship  # Tipado moderno para modelos ORM
from datetime import datetime  # Para manejar fechas de forma predeterminada
from database.db_postgres import Base  # Clase base declarativa SQLAlchemy
from core.enums import TipoTransaccion, EstadoTransaccion  # Enums definidos en el proyecto
from decimal import Decimal
# ─────────────────────────────────────────────────────────────────────────────
# Modelo ORM: Transaccion
# Representa una transacción bancaria entre dos cuentas
# ─────────────────────────────────────────────────────────────────────────────

class Transaccion(Base):
    __tablename__ = "transacciones"  # Nombre de la tabla en la base de datos

    # 🔑 ID único de la transacción (clave primaria, con índice para búsquedas rápidas)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 💸 FK a cuenta origen (quien envía el dinero)
    cuenta_origen_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id"),   # Relación con la tabla 'cuentas'
        nullable=False              # No se permite valor nulo
    )

    # 💰 FK a cuenta destino (quien recibe el dinero)
    cuenta_destino_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id"),   # Relación con la tabla 'cuentas'
        nullable=False              # Obligatorio
    )

    # 💵 Monto de dinero transferido en la transacción
    monto: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),             # Tipo de dato: número con decimales
        nullable=False              # Obligatorio
    )

    # 🏷️ Tipo de transacción (transferencia, depósito, retiro)
    tipo: Mapped[TipoTransaccion] = mapped_column(
        PgEnum(                     # Se define como ENUM en PostgreSQL
            TipoTransaccion,       # Enum que definimos en core.enums
            name="tipotransaccion",# Nombre del tipo ENUM en la base de datos
            create_constraint=False # Alembic crea el tipo en PostgreSQL
        ),
        nullable=False              # Obligatorio
    )

    # 📅 Fecha en la que se ejecutó la transacción (por defecto, ahora)
    fecha: Mapped[datetime] = mapped_column(
        default=datetime.now   # Asigna la fecha y hora actual automáticamente
    )

    # 📌 Estado de la transacción (completada, fallida, pendiente)
    estado: Mapped[EstadoTransaccion] = mapped_column(
        PgEnum(                     # Otro ENUM de PostgreSQL
            EstadoTransaccion,     # Enum definido
            name="estadotransaccion", # Nombre del ENUM en DB
            create_constraint=False
        ),
        default=EstadoTransaccion.completada  # Valor por defecto: completada
    )
    
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)

    # Organizacion donde se origina la transaccion. Nullable para migrar historico existente.
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizaciones.id"),
        nullable=True,
        index=True,
    )

    organizacion: Mapped["Organizacion | None"] = relationship(
        "Organizacion",
        back_populates="transacciones",
    )
    cuenta_origen: Mapped["Cuenta"] = relationship(
        "Cuenta",
        foreign_keys=[cuenta_origen_id],
        back_populates="transacciones_origen",
    )
    cuenta_destino: Mapped["Cuenta"] = relationship(
        "Cuenta",
        foreign_keys=[cuenta_destino_id],
        back_populates="transacciones_destino",
    )
