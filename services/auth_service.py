from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.usuario import Usuario
from core.seguridad import hash_password, verify_password, crear_token
from schemas.auth import RegistroUsuario, LoginUsuario, TokenRespuesta
from core.config import settings

# Función para registrar un nuevo usuario
def registrar_usuario(datos: RegistroUsuario, db: Session) -> Usuario:
    # Buscar si el email ya está registrado
    usuario_existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Hashear la contraseña ingresada por el usuario
    hashed_pw = hash_password(datos.password)

    # Crear instancia del modelo Usuario con los datos
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        hashed_password=hashed_pw
    )

    # Guardar en la base de datos
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario

# Función para loguear un usuario existente
def login_usuario(datos: LoginUsuario, db: Session) -> TokenRespuesta:
    # Buscar al usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales inválidas"
        )

    # Verificar si la contraseña coincide con la hasheada
    if not verify_password(datos.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales inválidas"
        )

    # Crear el token JWT con la info del usuario
    token_data = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }
    access_token = crear_token(token_data)

    # Devolver el token en un esquema estructurado
    return TokenRespuesta(access_token=access_token)
