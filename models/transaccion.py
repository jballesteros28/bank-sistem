from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, Integer, ForeignKey, String
from database.db_postgres import Base

class Transaccion(Base):
    __tablename__ = "transacciones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"))
    destino_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"))
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    tipo: Mapped[str] = mapped_column(String)  # transferencia, retiro, etc.
    estado: Mapped[str] = mapped_column(String, default="completada")
