from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum  # ✅ Enum nativo PostgreSQL
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from database.db_postgres import Base
from core.enums import RolUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    # 🔑 ID único del usuario
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 📛 Nombre completo del usuario
    nombre: Mapped[str] = mapped_column(String, nullable=False)

    # 📧 Email único
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # 🔐 Contraseña hasheada
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # ✅ Estado activo/inactivo
    es_activo: Mapped[bool] = mapped_column(Boolean, default=True)

    # 👤 Rol del usuario (cliente, admin, soporte)
    rol: Mapped[RolUsuario] = mapped_column(
        PgEnum(RolUsuario, name="rolusuario", create_constraint=False),
        default=RolUsuario.cliente,
        nullable=False
    )

    # ❌ Intentos fallidos de login
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ⏳ Bloqueo temporal de login
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Organizacion a la que pertenece el usuario. Es nullable para migrar datos existentes.
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizaciones.id"),
        nullable=True,
        index=True,
    )

    organizacion: Mapped["Organizacion | None"] = relationship(
        "Organizacion",
        back_populates="usuarios",
    )

    # Relacion con las cuentas del usuario, preservando el flujo usuario -> cuenta.
    cuentas: Mapped[list["Cuenta"]] = relationship("Cuenta", back_populates="usuario")

    # 🔗 Relación con tokens de reseteo de contraseña
    tokens_reset: Mapped[list["ResetPasswordToken"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
