from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoReglaRecompensa, MonedaRecompensa, TipoRecompensa


class ReglaRecompensa(Base):
    __tablename__ = "reglas_recompensa"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500))
    tipo: Mapped[TipoRecompensa] = mapped_column(
        Enum(
            TipoRecompensa,
            name="tipo_recompensa",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    estado: Mapped[EstadoReglaRecompensa] = mapped_column(
        Enum(
            EstadoReglaRecompensa,
            name="estado_regla_recompensa",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EstadoReglaRecompensa.activa,
    )
    porcentaje_cashback: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    monto_fijo: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    moneda_recompensa: Mapped[MonedaRecompensa] = mapped_column(
        Enum(
            MonedaRecompensa,
            name="moneda_recompensa",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=MonedaRecompensa.PUNTOS,
    )
    monto_minimo_compra: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    monto_maximo_recompensa: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    acumulable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    aplicaciones: Mapped[list["AplicacionRecompensa"]] = relationship(back_populates="regla")


class AplicacionRecompensa(Base):
    __tablename__ = "aplicaciones_recompensa"
    __table_args__ = (
        Index(
            "uq_aplicaciones_recompensa_org_referencia",
            "organizacion_id",
            "referencia_externa",
            unique=True,
            postgresql_where=text("referencia_externa IS NOT NULL"),
            sqlite_where=text("referencia_externa IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    regla_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reglas_recompensa.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    wallet_destino_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    movimiento_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("movimientos.id", ondelete="RESTRICT"),
        index=True,
    )
    monto_compra: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monto_recompensa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    moneda_recompensa: Mapped[MonedaRecompensa] = mapped_column(
        Enum(
            MonedaRecompensa,
            name="moneda_recompensa",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    referencia_externa: Mapped[str | None] = mapped_column(String(120), index=True)
    metadata_aplicacion: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    regla: Mapped[ReglaRecompensa] = relationship(back_populates="aplicaciones")
    usuario: Mapped["Usuario"] = relationship()
    wallet_destino: Mapped["Wallet"] = relationship()
    movimiento: Mapped["Movimiento | None"] = relationship()
