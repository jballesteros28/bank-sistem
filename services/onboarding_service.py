from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.enums.wallet_enum import MonedaWallet
from core.enums import EstadoCuenta, EstadoOrganizacion, RolUsuario, TipoCuenta
from core.seguridad import hash_password
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario
from schemas.onboarding_schema import (
    OnboardingOwnerResponse,
    OnboardingRegistroCreate,
    OnboardingRegistroResponse,
)
from schemas.organizacion_schema import OrganizacionResponse
from schemas.wallet_schema import WalletResponse
from services.cuenta_service import generar_numero_cuenta


def registrar_organizacion_con_owner(
    datos: OnboardingRegistroCreate,
    db: Session,
) -> OnboardingRegistroResponse:
    """Registra un tenant completo con owner y wallet principal en un commit."""
    slug = datos.organizacion.slug.strip().lower()
    owner_email = str(datos.owner.email).strip().lower()

    if db.query(Organizacion.id).filter(Organizacion.slug == slug).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una organizacion con ese slug.",
        )
    if db.query(Usuario.id).filter(Usuario.email == owner_email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email.",
        )

    try:
        organizacion = Organizacion(
            nombre=datos.organizacion.nombre.strip(),
            slug=slug,
            email_contacto=str(datos.organizacion.email_contacto).strip().lower(),
            estado=EstadoOrganizacion.activa,
        )
        db.add(organizacion)
        db.flush()

        owner = Usuario(
            nombre=datos.owner.nombre.strip(),
            email=owner_email,
            hashed_password=hash_password(datos.owner.password),
            es_activo=True,
            rol=RolUsuario.owner,
            intentos_fallidos=0,
            bloqueado_hasta=None,
            organizacion_id=organizacion.id,
        )
        db.add(owner)
        db.flush()

        wallet_principal = Cuenta(
            numero=generar_numero_cuenta(db),
            tipo=TipoCuenta.principal,
            alias="Wallet principal",
            moneda=MonedaWallet.ARS,
            saldo=Decimal("0.00"),
            limite_operacion=None,
            es_principal=True,
            estado=EstadoCuenta.activa,
            usuario_id=owner.id,
            organizacion_id=organizacion.id,
        )
        db.add(wallet_principal)
        db.flush()

        db.commit()
        db.refresh(organizacion)
        db.refresh(owner)
        db.refresh(wallet_principal)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return OnboardingRegistroResponse(
        organizacion=OrganizacionResponse.model_validate(organizacion),
        owner=OnboardingOwnerResponse.model_validate(owner),
        wallet_principal=WalletResponse.model_validate(wallet_principal),
    )

