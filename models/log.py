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
        fecha: Optional[datetime] = None
    ):
        self.evento = evento
        self.mensaje = mensaje
        self.nivel = nivel
        self.usuario_id = usuario_id
        self.endpoint = endpoint
        self.ip = ip
        self.metadata = metadata or {}
        self.fecha = fecha or datetime.utcnow()

    def dict(self):
        return self.__dict__