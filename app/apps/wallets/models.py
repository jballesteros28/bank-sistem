from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoWallet, MonedaWallet, TipoWallet


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4, index=True)
    alias: Mapped[str | None] = mapped_column(String(80))
    tipo: Mapped[TipoWallet] = mapped_column(
        Enum(
            TipoWallet,
            name="tipo_wallet",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=TipoWallet.principal,
    )
    estado: Mapped[EstadoWallet] = mapped_column(
        Enum(
            EstadoWallet,
            name="estado_wallet",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EstadoWallet.activa,
    )
    moneda: Mapped[MonedaWallet] = mapped_column(
        Enum(
            MonedaWallet,
            name="moneda_wallet",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=MonedaWallet.ARS,
    )
    saldo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    limite_operacion: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usuario_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    organizacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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

    usuario: Mapped["Usuario"] = relationship(back_populates="wallets")
    organizacion: Mapped["Organizacion"] = relationship(back_populates="wallets")
    movimientos_origen: Mapped[list["Movimiento"]] = relationship(
        foreign_keys="Movimiento.wallet_origen_id",
        back_populates="wallet_origen",
    )
    movimientos_destino: Mapped[list["Movimiento"]] = relationship(
        foreign_keys="Movimiento.wallet_destino_id",
        back_populates="wallet_destino",
    )
