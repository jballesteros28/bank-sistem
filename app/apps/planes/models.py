from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Plan(Base):
    __tablename__ = "planes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    precio_mensual: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    limite_usuarios: Mapped[int | None] = mapped_column(Integer)
    limite_wallets: Mapped[int | None] = mapped_column(Integer)
    limite_movimientos_mes: Mapped[int | None] = mapped_column(Integer)
    permite_webhooks: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    permite_white_label: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
