# models/reset_password.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer

from database.db_postgres import Base


class ResetPasswordToken(Base):
    """
    Modelo para almacenar tokens de recuperación de contraseña.
    Se asocia a un usuario y tiene un tiempo de expiración.
    """
    __tablename__ = "reset_password_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expiracion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relación con Usuario (opcional, para acceder al objeto desde el token)
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="tokens_reset")
