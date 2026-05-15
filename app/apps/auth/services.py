from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import LoginUsuario, RegistroUsuario, TokenRespuesta
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.limit_service import validar_limite_usuarios
from app.apps.usuarios.models import Usuario
from app.apps.usuarios.schemas import UsuarioResponse
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.shared.enums import RolUsuario
from app.shared.utils import normalize_email


LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def registrar_usuario(datos: RegistroUsuario, db: Session) -> UsuarioResponse:
    email = normalize_email(str(datos.email))
    organizacion = db.scalar(
        select(Organizacion).where(Organizacion.slug == datos.organizacion_slug)
    )
    if organizacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")

    if db.scalar(select(Usuario.id).where(Usuario.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya esta registrado.")

    validar_limite_usuarios(db, organizacion.id)

    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=email,
        hashed_password=hash_password(datos.password),
        rol=RolUsuario.cliente,
        organizacion_id=organizacion.id,
        es_activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)


def login_usuario(datos: LoginUsuario, db: Session) -> TokenRespuesta:
    email = normalize_email(str(datos.email))
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    now = datetime.now(timezone.utc)

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales invalidas.")

    if not usuario.es_activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo.")

    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario bloqueado temporalmente.")

    if not verify_password(datos.password, usuario.hashed_password):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= LOCKOUT_ATTEMPTS:
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = now + timedelta(minutes=LOCKOUT_MINUTES)
        db.add(usuario)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales invalidas.")

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.add(usuario)
    db.commit()

    access_token = create_access_token(
        {
            "sub": str(usuario.id),
            "email": usuario.email,
            "rol": usuario.rol.value,
            "organizacion_id": str(usuario.organizacion_id) if usuario.organizacion_id else None,
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenRespuesta(access_token=access_token)
