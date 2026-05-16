from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    evento: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    mensaje: Mapped[str] = mapped_column(String(500), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    actor_tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="usuario", index=True)
    actor_usuario_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("usuarios.id"))
    actor_api_key_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("api_keys.id"),
        index=True,
    )
    organizacion_id: Mapped[UUID | None] = mapped_column(
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

    actor_usuario: Mapped["Usuario | None"] = relationship(back_populates="audit_logs")
    actor_api_key: Mapped["APIKey | None"] = relationship(back_populates="audit_logs")
    organizacion: Mapped["Organizacion | None"] = relationship(back_populates="audit_logs")
