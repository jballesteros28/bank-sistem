from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, ForeignKey
from database.db_postgres import Base

class Cuenta(Base):
    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String, unique=True, index=True)
    tipo: Mapped[str] = mapped_column(String)  # ahorro, corriente, etc.
    saldo: Mapped[float] = mapped_column(Float, default=0.0)
    estado: Mapped[str] = mapped_column(String, default="activa")
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))

    # Relaciones opcionales (si usás backrefs o joins)
    # usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="cuentas")
