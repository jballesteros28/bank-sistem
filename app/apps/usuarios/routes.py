from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken
from app.apps.usuarios.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.apps.usuarios.services import crear_usuario, listar_usuarios, obtener_usuario, actualizar_usuario
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("", response_model=ApiResponse[UsuarioResponse], status_code=status.HTTP_201_CREATED)
def post_usuario(
    datos: UsuarioCreate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UsuarioResponse]:
    return ok(crear_usuario(datos, current_user, db), "Usuario creado correctamente.")


@router.get("", response_model=ApiResponse[list[UsuarioResponse]])
def get_usuarios(
    organizacion_id: UUID | None = Query(default=None),
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[UsuarioResponse]]:
    return ok(listar_usuarios(current_user, db, organizacion_id), "Usuarios obtenidos correctamente.")


@router.get("/{usuario_id}", response_model=ApiResponse[UsuarioResponse])
def get_usuario(
    usuario_id: int,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UsuarioResponse]:
    return ok(obtener_usuario(usuario_id, current_user, db), "Usuario obtenido correctamente.")


@router.patch("/{usuario_id}", response_model=ApiResponse[UsuarioResponse])
def patch_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UsuarioResponse]:
    return ok(actualizar_usuario(usuario_id, datos, current_user, db), "Usuario actualizado correctamente.")

