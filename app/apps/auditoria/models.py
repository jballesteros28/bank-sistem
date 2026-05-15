from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evento: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    mensaje: Mapped[str] = mapped_column(String(500), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    actor_usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id"),
        index=True,
    )
    endpoint: Mapped[str | None] = mapped_column(String(255))
    ip: Mapped[str | None] = mapped_column(String(80))
    metadata_log: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

