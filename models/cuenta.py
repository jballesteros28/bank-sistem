from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Integer, ForeignKey
from database.db_postgres import Base
from core.enums import TipoCuenta, EstadoCuenta

class Cuenta(Base):
    __tablename__ = "cuentas"

    # 🔑 Identificador único de la cuenta
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 📄 Número de cuenta único
    numero: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # 💳 Tipo de cuenta (ej: ahorro, corriente, sueldo, etc.)
    tipo: Mapped[TipoCuenta] = mapped_column(nullable=False)

    # 💰 Saldo actual de la cuenta
    saldo: Mapped[float] = mapped_column(Float, default=0.0)

    # 📌 Estado de la cuenta (activa, inactiva, congelada)
    estado: Mapped[EstadoCuenta] = mapped_column(default=EstadoCuenta.activa)

    # 🔗 Relación con el usuario dueño de la cuenta
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
