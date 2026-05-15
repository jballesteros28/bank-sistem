from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.apps.auth.dependencies import get_current_user
from app.apps.auth.schemas import DatosUsuarioToken, LoginUsuario, RegistroUsuario, TokenRespuesta
from app.apps.auth.services import login_usuario, registrar_usuario
from app.apps.usuarios.models import Usuario
from app.apps.usuarios.schemas import UsuarioResponse
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[UsuarioResponse], status_code=status.HTTP_201_CREATED)
def register(datos: RegistroUsuario, db: Session = Depends(get_db)) -> ApiResponse[UsuarioResponse]:
    usuario = registrar_usuario(datos, db)
    return ok(usuario, "Usuario registrado correctamente.")


@router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginUsuario, db: Session = Depends(get_db)) -> TokenRespuesta:
    return login_usuario(datos, db)


@router.get("/me", response_model=ApiResponse[UsuarioResponse])
def me(
    current_user: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UsuarioResponse]:
    usuario = db.get(Usuario, current_user.id)
    if usuario is None:
        raise RuntimeError("Authenticated user disappeared during request.")
    return ok(UsuarioResponse.model_validate(usuario), "Usuario actual obtenido correctamente.")

