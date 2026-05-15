from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.usuarios.models import Usuario
from app.core.api import API_V1_PREFIX
from app.core.database import get_db
from app.core.permissions import is_admin, is_super_admin
from app.core.security import decode_access_token
from app.shared.enums import RolUsuario


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> DatosUsuarioToken:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado.",
        )

    usuario = db.get(Usuario, user_id)
    if usuario is None or not usuario.es_activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo.",
        )

    return DatosUsuarioToken(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=RolUsuario(str(usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol)),
        organizacion_id=usuario.organizacion_id,
    )


def get_current_admin(
    current_user: DatosUsuarioToken = Depends(get_current_user),
) -> DatosUsuarioToken:
    if not is_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a administradores.")
    return current_user


def get_current_super_admin(
    current_user: DatosUsuarioToken = Depends(get_current_user),
) -> DatosUsuarioToken:
    if not is_super_admin(current_user.rol):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a super_admin.")
    return current_user

