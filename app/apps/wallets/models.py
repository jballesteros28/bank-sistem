from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import EstadoWallet, MonedaWallet, OwnerTypeWallet, TipoWallet


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint(
            "("
            "owner_type = 'usuario' AND usuario_id IS NOT NULL AND organizacion_owner_id IS NULL"
            ") OR ("
            "owner_type = 'organizacion' AND organizacion_owner_id IS NOT NULL AND usuario_id IS NULL"
            ")",
            name="ck_wallet_owner_consistency",
        ),
    )

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
    owner_type: Mapped[OwnerTypeWallet] = mapped_column(
        Enum(
            OwnerTypeWallet,
            name="owner_type_wallet",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=OwnerTypeWallet.usuario,
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )
    organizacion_owner_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=True,
    )
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

    usuario: Mapped["Usuario | None"] = relationship(back_populates="wallets")
    organizacion: Mapped["Organizacion"] = relationship(
        back_populates="wallets",
        foreign_keys=[organizacion_id],
    )
    organizacion_owner: Mapped["Organizacion | None"] = relationship(
        foreign_keys=[organizacion_owner_id],
    )
    movimientos_origen: Mapped[list["Movimiento"]] = relationship(
        foreign_keys="Movimiento.wallet_origen_id",
        back_populates="wallet_origen",
    )
    movimientos_destino: Mapped[list["Movimiento"]] = relationship(
        foreign_keys="Movimiento.wallet_destino_id",
        back_populates="wallet_destino",
    )
