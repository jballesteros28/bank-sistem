from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import CanalNotificacion, TipoNotificacion


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    usuario_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoNotificacion] = mapped_column(
        Enum(
            TipoNotificacion,
            name="tipo_notificacion",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    canal: Mapped[CanalNotificacion] = mapped_column(
        Enum(
            CanalNotificacion,
            name="canal_notificacion",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=CanalNotificacion.interna,
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_notificacion: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    leida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enviada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_envio: Mapped[str | None] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_lectura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario: Mapped["Usuario | None"] = relationship(back_populates="notificaciones")
    organizacion: Mapped["Organizacion | None"] = relationship(back_populates="notificaciones")
