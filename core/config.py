from pydantic_settings import BaseSettings
from pydantic import EmailStr


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    # MongoDB
    MONGO_URI: str
    MONGO_DB: str

    # Seguridad JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Configuración FastAPI-Mail
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True  
    MAIL_SSL_TLS: bool = False 

    class Config:
        env_file = ".env"
        extra = "forbid"

settings = Settings()


