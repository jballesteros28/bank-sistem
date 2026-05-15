from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.organizaciones.dependencies import resolve_organization_scope
from app.apps.organizaciones.models import Organizacion
from app.apps.usuarios.models import Usuario
from app.apps.usuarios.permissions import ensure_can_manage_users, ensure_role_is_assignable
from app.apps.usuarios.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.core.permissions import is_super_admin
from app.core.security import hash_password
from app.shared.enums import RolUsuario
from app.shared.utils import normalize_email


def _resolve_target_organization(
    datos_organizacion_id: UUID | None,
    current_user: DatosUsuarioToken,
    db: Session,
) -> UUID | None:
    target_id = resolve_organization_scope(current_user, datos_organizacion_id)
    if target_id is not None and db.get(Organizacion, target_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacion no encontrada.")
    return target_id


def crear_usuario(
    datos: UsuarioCreate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> UsuarioResponse:
    ensure_can_manage_users(current_user)
    ensure_role_is_assignable(current_user, datos.rol)
    email = normalize_email(str(datos.email))

    if db.scalar(select(Usuario.id).where(Usuario.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya esta registrado.")

    organizacion_id = _resolve_target_organization(datos.organizacion_id, current_user, db)
    if organizacion_id is None and datos.rol != RolUsuario.super_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario requiere organizacion.")

    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=email,
        hashed_password=hash_password(datos.password),
        rol=datos.rol,
        organizacion_id=organizacion_id,
        es_activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)


def listar_usuarios(
    current_user: DatosUsuarioToken,
    db: Session,
    organizacion_id: UUID | None = None,
) -> list[UsuarioResponse]:
    ensure_can_manage_users(current_user)
    scope_id = resolve_organization_scope(current_user, organizacion_id)
    query = select(Usuario).order_by(Usuario.id.asc())
    if scope_id is not None:
        query = query.where(Usuario.organizacion_id == scope_id)
    elif not is_super_admin(current_user.rol):
        query = query.where(Usuario.organizacion_id == current_user.organizacion_id)
    return [UsuarioResponse.model_validate(usuario) for usuario in db.scalars(query).all()]


def obtener_usuario(usuario_id: int, current_user: DatosUsuarioToken, db: Session) -> UsuarioResponse:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if not is_super_admin(current_user.rol) and usuario.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if current_user.id != usuario.id:
        ensure_can_manage_users(current_user)
    return UsuarioResponse.model_validate(usuario)


def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    current_user: DatosUsuarioToken,
    db: Session,
) -> UsuarioResponse:
    ensure_can_manage_users(current_user)
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if not is_super_admin(current_user.rol) and usuario.organizacion_id != current_user.organizacion_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    cambios = datos.model_dump(exclude_unset=True)
    if "rol" in cambios:
        ensure_role_is_assignable(current_user, cambios["rol"])
    for field, value in cambios.items():
        setattr(usuario, field, value)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)

