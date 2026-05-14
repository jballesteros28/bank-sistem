from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, NUMERIC, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums.wallet_enum import MonedaWallet
from core.enums import EstadoCuenta, TipoCuenta
from database.db_postgres import Base


class Cuenta(Base):
    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Se mantiene el campo historico para no romper /cuentas; Fase 3 agrega
    # valores compatibles con wallets en el enum existente de PostgreSQL.
    tipo: Mapped[TipoCuenta] = mapped_column(
        SQLEnum(TipoCuenta, name="tipocuenta", create_constraint=False),
        nullable=False,
    )

    # Campos SaaS de wallet agregados sobre la tabla existente "cuentas".
    alias: Mapped[str | None] = mapped_column(String(80), nullable=True)
    moneda: Mapped[MonedaWallet] = mapped_column(
        SQLEnum(MonedaWallet, name="moneda_wallet", create_constraint=False),
        nullable=False,
        default=MonedaWallet.ARS,
        server_default=MonedaWallet.ARS.value,
    )
    limite_operacion: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    es_principal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    saldo: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=0)
    estado: Mapped[EstadoCuenta] = mapped_column(
        SQLEnum(EstadoCuenta, name="estadocuenta", create_constraint=False),
        default=EstadoCuenta.activa,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    # Organizacion propietaria de la cuenta. Nullable permite migrar cuentas existentes.
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizaciones.id"),
        nullable=True,
        index=True,
    )

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="cuentas")
    organizacion: Mapped["Organizacion | None"] = relationship(
        "Organizacion",
        back_populates="cuentas",
    )
    transacciones_origen: Mapped[list["Transaccion"]] = relationship(
        "Transaccion",
        foreign_keys="Transaccion.cuenta_origen_id",
        back_populates="cuenta_origen",
    )
    transacciones_destino: Mapped[list["Transaccion"]] = relationship(
        "Transaccion",
        foreign_keys="Transaccion.cuenta_destino_id",
        back_populates="cuenta_destino",
    )
