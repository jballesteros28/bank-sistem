from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from schemas.auth import DatosUsuarioToken
from sqlalchemy.orm import Session
from database.db_postgres import SessionLocal
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def crear_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)




# Definir el esquema Bearer para extraer el token automáticamente
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para obtener el usuario actual desde el token JWT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DatosUsuarioToken:
    try:
        # Decodificar el token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Validar datos esenciales
        id = payload.get("id")
        email = payload.get("email")
        nombre = payload.get("nombre")
        rol = payload.get("rol")

        if not all([id, email, nombre, rol]):
            raise HTTPException(status_code=401, detail="Token inválido")

        return DatosUsuarioToken(id=id, email=email, nombre=nombre, rol=rol)

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
