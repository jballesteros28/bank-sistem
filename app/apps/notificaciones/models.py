from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.enums import EstadoNotificacion, TipoNotificacion


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id"),
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
    estado: Mapped[EstadoNotificacion] = mapped_column(
        Enum(
            EstadoNotificacion,
            name="estado_notificacion",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EstadoNotificacion.queued,
    )
    asunto: Mapped[str] = mapped_column(String(180), nullable=False)
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

