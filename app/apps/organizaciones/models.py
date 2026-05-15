from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoOrganizacion


class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    email_contacto: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoOrganizacion] = mapped_column(
        Enum(
            EstadoOrganizacion,
            name="estado_organizacion",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EstadoOrganizacion.activa,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="organizacion")
    wallets: Mapped[list["Wallet"]] = relationship(back_populates="organizacion")
    movimientos: Mapped[list["Movimiento"]] = relationship(back_populates="organizacion")
