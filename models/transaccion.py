from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, Integer, ForeignKey, String, DateTime
from datetime import datetime
from database.db_postgres import Base

class Transaccion(Base):
    __tablename__ = "transacciones"

    # 🔑 ID único de la transacción
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 💸 Cuenta de origen (FK a cuenta.id)
    cuenta_origen_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"), nullable=False)

    # 💰 Cuenta de destino (FK a cuenta.id)
    cuenta_destino_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"), nullable=False)

    # 💵 Monto transferido
    monto: Mapped[float] = mapped_column(Float, nullable=False)

    # 🏷️ Tipo de transacción (ej: transferencia, depósito, retiro)
    tipo: Mapped[str] = mapped_column(String, nullable=False)

    # 📅 Fecha y hora de la transacción
    fecha: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 📌 Estado de la transacción (ej: completada, fallida, pendiente)
    estado: Mapped[str] = mapped_column(String, default="completada")
