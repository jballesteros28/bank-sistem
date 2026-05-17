from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EcommerceOrderEvent(Base):
    __tablename__ = "ecommerce_order_events"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_ecommerce_order_events_amount_positive"),
        Index(
            "uq_ecommerce_order_events_org_provider_order",
            "organizacion_id",
            "proveedor",
            "external_order_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proveedor: Mapped[str] = mapped_column(String(60), nullable=False)
    external_order_id: Mapped[str] = mapped_column(String(160), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(20), nullable=False, default="ARS")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="paid", index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    procesado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    recompensa_aplicada_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("aplicaciones_recompensa.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    error_procesamiento: Mapped[str | None] = mapped_column(String(500))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_procesamiento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organizacion: Mapped["Organizacion"] = relationship()
    recompensa_aplicada: Mapped["AplicacionRecompensa | None"] = relationship()
