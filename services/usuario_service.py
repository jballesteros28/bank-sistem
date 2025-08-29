from sqlalchemy.orm import Session
from models.usuario import Usuario
from schemas.usuario import UsuarioOut
from fastapi import HTTPException, status

# 🧾 Obtener los datos del perfil del usuario autenticado
def obtener_usuario_actual(usuario_id: int, db: Session) -> UsuarioOut:
    # Buscar el usuario en la base de datos por su ID
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    # Validar que exista y esté activo
    if not usuario or not usuario.es_activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no existe o está desactivado"
        )

    # Devolver el esquema estructurado de salida
    return UsuarioOut.model_validate(usuario)
