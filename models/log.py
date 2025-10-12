# models/log.py
from datetime import datetime
from typing import Optional, Dict, Any

class LogMongo:
    def __init__(
        self,
        evento: str,
        mensaje: str,
        nivel: str = "INFO",
        usuario_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        ip: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fecha: Optional[datetime] = None,
        correlation_id: Optional[str] = None  # 🔑 Nuevo campo
    ):
        self.evento = evento
        self.mensaje = mensaje
        self.nivel = nivel
        self.usuario_id = usuario_id
        self.endpoint = endpoint
        self.ip = ip
        self.metadata = metadata or {}
        self.fecha = fecha or datetime.utcnow()
        self.correlation_id = correlation_id  # guardamos ID único del request

    def dict(self) -> Dict[str, Any]:
        return self.__dict__

# 📧 Log específico para correos
class LogCorreo:
    def __init__(
        self,
        destinatario: str,
        asunto: str,
        template: str,
        estado: str,
        error: Optional[str] = None,
        fecha: Optional[datetime] = None,
        correlation_id: Optional[str] = None  # 🔑 También para correos
    ):
        self.destinatario = destinatario
        self.asunto = asunto
        self.template = template
        self.estado = estado   # "ENVIADO" o "ERROR"
        self.error = error
        self.fecha = fecha or datetime.utcnow()
        self.correlation_id = correlation_id

    def dict(self) -> Dict[str, Any]:
        return self.__dict__
