from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from schemas.usuario import UsuarioOut
from core.seguridad import get_current_user
from schemas.auth import DatosUsuarioToken
from services.usuario_service import obtener_usuario_actual
from core.dependencias import get_db

# Crear el router del módulo de usuarios
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# 🧾 Endpoint: Obtener perfil del usuario autenticado
@router.get("/me", response_model=UsuarioOut, status_code=status.HTTP_200_OK)
def perfil_usuario_actual(
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna los datos del usuario actualmente autenticado usando el token JWT.
    """
    return obtener_usuario_actual(usuario_token.id, db)
