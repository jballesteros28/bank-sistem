from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoMovimiento, TipoMovimiento


class Movimiento(Base):
    __tablename__ = "movimientos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    wallet_origen_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    wallet_destino_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tipo: Mapped[TipoMovimiento] = mapped_column(
        Enum(
            TipoMovimiento,
            name="tipo_movimiento",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    estado: Mapped[EstadoMovimiento] = mapped_column(
        Enum(
            EstadoMovimiento,
            name="estado_movimiento",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EstadoMovimiento.aprobada,
    )
    descripcion: Mapped[str | None] = mapped_column(String(255))
    referencia_externa: Mapped[str | None] = mapped_column(String(120), index=True)
    metadata_movimiento: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    movimiento_origen_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("movimientos.id"),
        index=True,
    )
    es_reversa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    motivo_reversa: Mapped[str | None] = mapped_column(String(255))
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organizacion: Mapped["Organizacion"] = relationship(back_populates="movimientos")
    wallet_origen: Mapped["Wallet"] = relationship(
        foreign_keys=[wallet_origen_id],
        back_populates="movimientos_origen",
    )
    wallet_destino: Mapped["Wallet"] = relationship(
        foreign_keys=[wallet_destino_id],
        back_populates="movimientos_destino",
    )
    movimiento_origen: Mapped["Movimiento | None"] = relationship(remote_side=[id])
