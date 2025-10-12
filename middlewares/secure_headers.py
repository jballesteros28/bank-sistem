from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# 🔐 Middleware de seguridad para agregar encabezados HTTP
# Protege contra ataques comunes como sniffing de tipos, XSS o clickjacking
class SecureHeadersMiddleware(BaseHTTPMiddleware):

    # Método principal que intercepta todas las requests
    async def dispatch(
        self,
        request: Request,  # 📥 La petición HTTP entrante
        call_next: Callable[[Request], Awaitable[Response]]  # 🔄 Función que procesa la request y devuelve la respuesta
    ) -> Response:  # 📤 Devuelve una Response al cliente
        # ⏩ Pasa la request al siguiente middleware o endpoint
        response: Response = await call_next(request)

        # 🚧 Agregar cabeceras de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        # ❌ Impide que el navegador interprete archivos con un tipo MIME incorrecto

        response.headers["X-Frame-Options"] = "DENY"
        # ❌ Evita que el sitio se incruste en iframes (previene clickjacking)

        response.headers["X-XSS-Protection"] = "1; mode=block"
        # 🛡️ Activa protección contra ataques XSS en navegadores antiguos

        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        # 🔒 Obliga a usar HTTPS durante 1 año en todo el dominio y subdominios

        # 📤 Devuelve la respuesta final al cliente con los headers extra
        return response
