from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import EstadoOrganizacion
from database.db_postgres import Base


class Organizacion(Base):
    __tablename__ = "organizaciones"

    # Identificador publico y estable para separar datos por organizacion.
    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Datos basicos de identificacion y contacto de la organizacion.
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email_contacto: Mapped[str] = mapped_column(String, nullable=False)

    # Estado operativo de la organizacion dentro del SaaS.
    estado: Mapped[EstadoOrganizacion] = mapped_column(
        PgEnum(EstadoOrganizacion, name="estado_organizacion", create_constraint=False),
        default=EstadoOrganizacion.activa,
        nullable=False,
    )

    # Auditoria minima de creacion y ultima actualizacion.
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        onupdate=datetime.now,
        nullable=True,
    )

    # Relaciones iniciales del modelo multi-organizacion.
    usuarios: Mapped[list["Usuario"]] = relationship("Usuario", back_populates="organizacion")
    cuentas: Mapped[list["Cuenta"]] = relationship("Cuenta", back_populates="organizacion")
    transacciones: Mapped[list["Transaccion"]] = relationship(
        "Transaccion",
        back_populates="organizacion",
    )
