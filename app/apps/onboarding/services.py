from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.onboarding.schemas import OnboardingRegistroCreate, OnboardingRegistroResponse
from app.apps.organizaciones.models import Organizacion
from app.apps.organizaciones.schemas import OrganizacionResponse
from app.apps.usuarios.models import Usuario
from app.apps.usuarios.schemas import UsuarioResponse
from app.apps.wallets.models import Wallet
from app.apps.wallets.schemas import WalletResponse
from app.core.security import hash_password
from app.shared.enums import EstadoOrganizacion, EstadoWallet, MonedaWallet, RolUsuario, TipoWallet
from app.shared.utils import normalize_email


def registrar_organizacion_con_owner(
    datos: OnboardingRegistroCreate,
    db: Session,
) -> OnboardingRegistroResponse:
    slug = datos.organizacion.slug.strip().lower()
    owner_email = normalize_email(str(datos.owner.email))

    if db.scalar(select(Organizacion.id).where(Organizacion.slug == slug)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una organizacion con ese slug.")
    if db.scalar(select(Usuario.id).where(Usuario.email == owner_email)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un usuario con ese email.")

    try:
        organizacion = Organizacion(
            nombre=datos.organizacion.nombre.strip(),
            slug=slug,
            email_contacto=normalize_email(str(datos.organizacion.email_contacto)),
            estado=EstadoOrganizacion.activa,
        )
        db.add(organizacion)
        db.flush()

        owner = Usuario(
            nombre=datos.owner.nombre.strip(),
            email=owner_email,
            hashed_password=hash_password(datos.owner.password),
            rol=RolUsuario.owner,
            es_activo=True,
            organizacion_id=organizacion.id,
        )
        db.add(owner)
        db.flush()

        wallet_principal = Wallet(
            alias="Wallet principal",
            tipo=TipoWallet.principal,
            estado=EstadoWallet.activa,
            moneda=MonedaWallet.ARS,
            saldo=Decimal("0.00"),
            limite_operacion=None,
            es_principal=True,
            usuario_id=owner.id,
            organizacion_id=organizacion.id,
        )
        db.add(wallet_principal)
        db.commit()
        db.refresh(organizacion)
        db.refresh(owner)
        db.refresh(wallet_principal)
    except Exception:
        db.rollback()
        raise

    return OnboardingRegistroResponse(
        organizacion=OrganizacionResponse.model_validate(organizacion),
        owner=UsuarioResponse.model_validate(owner),
        wallet_principal=WalletResponse.model_validate(wallet_principal),
    )

