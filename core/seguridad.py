from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from schemas.auth import DatosUsuarioToken
from sqlalchemy.orm import Session
from core.config import settings
from services.log_service import guardar_log
from models.log import LogMongo
from core.dependencias import get_db

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


# Función para obtener el usuario actual desde el token JWT
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), request: Request = None) -> DatosUsuarioToken:
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
        log = LogMongo(
        evento="TokenInvalido",
        mensaje="Se intentó acceder con un token inválido o expirado.",
        nivel="WARNING",
        endpoint=str(request.url),
        ip=request.client.host
        )
        await guardar_log(log)
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
