from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultimo_uso_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_revocacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organizacion: Mapped["Organizacion"] = relationship()


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    eventos: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    secret_encrypted: Mapped[str] = mapped_column(String(1000), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organizacion: Mapped["Organizacion"] = relationship()
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(back_populates="webhook_endpoint")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    webhook_endpoint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("webhook_endpoints.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    evento: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendiente", index=True)
    status_code: Mapped[int | None] = mapped_column(Integer)
    respuesta_body: Mapped[str | None] = mapped_column(Text)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_ultimo_intento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organizacion: Mapped["Organizacion"] = relationship()
    webhook_endpoint: Mapped[WebhookEndpoint] = relationship(back_populates="deliveries")
