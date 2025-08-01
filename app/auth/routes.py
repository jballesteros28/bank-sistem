from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database.db_postgres import SessionLocal
from schemas.auth import RegistroUsuario, LoginUsuario, TokenRespuesta
from services.auth_service import registrar_usuario, login_usuario

# Crear router para autenticación
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint: registrar nuevo usuario
@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroUsuario, db: Session = Depends(get_db)):
    usuario = registrar_usuario(datos, db)
    return {
        "msg": "Usuario registrado exitosamente",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol
        }
    }

# Endpoint: login de usuario y retorno de JWT
@router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginUsuario, db: Session = Depends(get_db)):
    return login_usuario(datos, db)



from core.seguridad import get_current_user
from schemas.auth import DatosUsuarioToken

# 🔐 Ruta protegida: devuelve los datos del usuario autenticado
@router.get("/me", response_model=DatosUsuarioToken)
def obtener_usuario_actual(usuario: DatosUsuarioToken = Depends(get_current_user)):
    return usuario
