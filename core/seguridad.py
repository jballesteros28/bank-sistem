# core/seguridad.py
# -*- coding: utf-8 -*-

from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Any

from core.config import settings
from core.dependencias import get_db
from core.enums import RolUsuario
from models.usuario import Usuario
from schemas.auth import DatosUsuarioToken
from services.log_service import guardar_log
from models.log import LogMongo

# ==========================================================
# 🔐 Configuración general
# ==========================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def is_super_admin(current_user: DatosUsuarioToken) -> bool:
    """Indica si el usuario autenticado tiene permisos globales SaaS."""
    return current_user.rol == RolUsuario.SUPER_ADMIN.value


def is_admin_or_super_admin(current_user: DatosUsuarioToken) -> bool:
    """Centraliza la regla para rutas administrativas existentes."""
    return current_user.rol in {RolUsuario.admin.value, RolUsuario.SUPER_ADMIN.value}


# ==========================================================
# 🔒 Helpers de hash
# ==========================================================

def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que una contraseña plana coincida con su hash."""
    return pwd_context.verify(plain, hashed)


# ==========================================================
# 🧩 Creación de token JWT
# ==========================================================

def crear_token(data: dict[Any, Any], expires_delta: timedelta | None = None) -> str:
    """
    Crea un JWT válido con expiración segura en UTC.
    """
    to_encode = data.copy()

    exp_val = to_encode.get("exp")
    if exp_val is None:
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode["exp"] = expire
    elif isinstance(exp_val, datetime) and exp_val.tzinfo is None:
        to_encode["exp"] = exp_val.replace(tzinfo=timezone.utc)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ==========================================================
# 👤 Obtener usuario autenticado desde el token
# ==========================================================

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> DatosUsuarioToken:
    """
    Decodifica el token JWT, valida expiración y existencia del usuario activo.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )

        user_id = payload.get("id")
        email = payload.get("email")
        nombre = payload.get("nombre")
        rol = payload.get("rol")

        if not all([user_id, email, nombre, rol]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        usuario: Usuario | None = (
            db.query(Usuario)
            .filter(Usuario.id == user_id, Usuario.es_activo == True)
            .first()
        )

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
            )

        # ✅ Retornar datos del usuario autenticado
        return DatosUsuarioToken(
            id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol,
            organizacion_id=usuario.organizacion_id,
        )

    # 🚫 Token expirado
    except ExpiredSignatureError:
        log = LogMongo(
            evento="TokenInvalido",
            mensaje="Intento de acceso con token expirado.",
            nivel="WARNING",
            endpoint=str(request.url),
            ip=request.client.host,
        )
        await guardar_log(log)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )

    # 🚫 Token inválido o manipulado
    except JWTError:
        log = LogMongo(
            evento="TokenInvalido",
            mensaje="Intento de acceso con token inválido o manipulado.",
            nivel="WARNING",
            endpoint=str(request.url),
            ip=request.client.host,
        )
        await guardar_log(log)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


# ==========================================================
# 👮‍♂️ Obtener usuario administrador (autorización)
# ==========================================================

async def get_current_admin(
    request: Request,
    current_user: DatosUsuarioToken = Depends(get_current_user),
) -> DatosUsuarioToken:
    """
    Permite acceso a usuarios con rol 'admin' o 'super_admin'.
    Si no cumple, registra un log en Mongo y lanza 403.
    """
    if not is_admin_or_super_admin(current_user):
        log = LogMongo(
            evento="AccesoNoAutorizado",
            mensaje=f"Usuario {current_user.email} intentó acceder a una ruta administrativa.",
            nivel="WARNING",
            usuario_id=current_user.id,
            endpoint=str(request.url),
            ip=request.client.host,
        )
        await guardar_log(log)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores",
        )

    return current_user


async def get_current_super_admin(
    request: Request,
    current_user: DatosUsuarioToken = Depends(get_current_user),
) -> DatosUsuarioToken:
    """Permite solo usuarios con rol global super_admin."""
    if not is_super_admin(current_user):
        log = LogMongo(
            evento="AccesoNoAutorizado",
            mensaje=f"Usuario {current_user.email} intento acceder a una ruta de super admin.",
            nivel="WARNING",
            usuario_id=current_user.id,
            endpoint=str(request.url),
            ip=request.client.host,
        )
        await guardar_log(log)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a super administradores",
        )

    return current_user
