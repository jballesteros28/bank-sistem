from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoOrganizacion


class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    email_contacto: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_comercial: Mapped[str | None] = mapped_column(String(150))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    color_primario: Mapped[str | None] = mapped_column(String(7))
    color_secundario: Mapped[str | None] = mapped_column(String(7))
    subdominio: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    dominio_personalizado: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    moneda_default: Mapped[str] = mapped_column(String(20), nullable=False, default="ARS")
    timezone: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="America/Argentina/Buenos_Aires",
    )
    permite_white_label_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("planes.id"),
        nullable=True,
    )
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
    wallets: Mapped[list["Wallet"]] = relationship(
        back_populates="organizacion",
        foreign_keys="Wallet.organizacion_id",
    )
    movimientos: Mapped[list["Movimiento"]] = relationship(back_populates="organizacion")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="organizacion")
    notificaciones: Mapped[list["Notificacion"]] = relationship(back_populates="organizacion")
    plan: Mapped["Plan | None"] = relationship()
