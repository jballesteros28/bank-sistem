# ─────────────────────────────────────────────────────────────────────────────
# Importaciones necesarias
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import NUMERIC, ForeignKey, String
# Tipos de columnas de SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM as PgEnum  # ENUM nativo de PostgreSQL
from sqlalchemy.orm import Mapped, mapped_column  # Tipado moderno para modelos ORM
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
        default=datetime.utcnow    # Asigna la fecha y hora actual automáticamente
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
    
    descripcion: Mapped[str] = mapped_column(String, nullable=True)
