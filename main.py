# main.py
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ─────────────── Rutas de la aplicación ───────────────
from app.auth import routes as auth_routes
from app.usuarios import routes as usuarios_routes
from app.cuentas import routes as cuentas_routes
from app.transacciones import routes as transacciones_routes
from app.organizaciones import routes as organizaciones_routes
from app.admin import routes as admin_routes
from app.admin import log_routes
from app.notificaciones import routes as notificaciones_routes

# ─────────────── Manejadores de errores ───────────────
from core.excepciones import (
    manejar_errores_validacion,
    manejar_http_exception,
    manejar_error_general,
    manejar_error_sqlalchemy,
    manejar_cuenta_congelada,
    respuesta_error_estandar,
    CuentaCongeladaError,
    SaldoInsuficienteError,
)

# ─────────────── Servicios y logs ───────────────
from services.log_service import guardar_log, correlation_id_ctx
from services.transaccion_service import manejar_saldo_insuficiente
from models.log import LogMongo

# ─────────────── Seguridad y middlewares ───────────────
from fastapi.middleware.cors import CORSMiddleware
from middlewares.secure_headers import SecureHeadersMiddleware

# ─────────────── Rate Limiting ───────────────
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ─────────────── Utilidades ───────────────
import uuid


# ==========================================================
# 🚀 Inicialización principal de la app
# ==========================================================
app = FastAPI(
    title="Sistema Bancario",
    version="1.0",
    description="API central del sistema bancario con autenticación, cuentas, transacciones, administración y notificaciones.",
)


# ==========================================================
# 🧩 Middleware: Correlation ID
# ==========================================================
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """
    Asigna un identificador único (UUID) a cada request.
    Este ID se usa para trazar logs, errores y respuestas en todo el sistema.
    """
    correlation_id = str(uuid.uuid4())
    correlation_id_ctx.set(correlation_id)

    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ==========================================================
# 🌐 CORS (Cross-Origin Resource Sharing)
# ==========================================================
origins = [
    "http://localhost:3000",    # Desarrollo local
    "https://mi-frontend.com",  # Producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# 🧱 Middlewares de Seguridad
# ==========================================================
app.add_middleware(SecureHeadersMiddleware)


# ==========================================================
# 🚦 Rate Limiting (control de solicitudes por IP)
# ==========================================================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Limita el número de solicitudes por cliente.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Demasiadas solicitudes. Intente más tarde."},
    )


# ==========================================================
# ⚙️ Manejadores globales de errores
# ==========================================================
app.add_exception_handler(RequestValidationError, manejar_errores_validacion)
app.add_exception_handler(StarletteHTTPException, manejar_http_exception)
app.add_exception_handler(SQLAlchemyError, manejar_error_sqlalchemy)
app.add_exception_handler(CuentaCongeladaError, manejar_cuenta_congelada)
app.add_exception_handler(SaldoInsuficienteError, manejar_saldo_insuficiente)
app.add_exception_handler(Exception, manejar_error_general)


# ==========================================================
# 🧭 Registro de routers
# ==========================================================
app.include_router(auth_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(cuentas_routes.router)
app.include_router(transacciones_routes.router)
app.include_router(organizaciones_routes.router)
app.include_router(admin_routes.router)
app.include_router(notificaciones_routes.router)
# 📊 Logs administrativos
app.include_router(log_routes.router)


# ==========================================================
# 🚫 Manejador de rutas no encontradas (404)
# ==========================================================
@app.exception_handler(404)
async def ruta_no_encontrada(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    📌 Captura global de errores 404 con distinción entre:
    - Errores de negocio (e.g., "Usuario no encontrado" / "Cuenta no encontrada")
    - Rutas inexistentes reales (no definidas en la API)
    """

    detalle_lower = str(exc.detail).lower() if exc.detail else ""

    # ✅ Caso 1: Error legítimo del dominio
    if "no encontrado" in detalle_lower or "no encontrada" in detalle_lower:
        return respuesta_error_estandar(
            detalle=exc.detail,
            status_code=404,
            error_type="RecursoNoEncontrado",
        )

    # ⚠️ Caso 2: Ruta realmente inexistente
    # log = LogMongo(
    #     evento="RutaNoEncontrada",
    #     mensaje=f"Intento de acceder a una ruta inexistente: {request.url.path}",
    #     nivel="WARNING",
    #     ip=request.client.host if request.client else None,
    #     correlation_id=getattr(request.state, "correlation_id", None),
    #     metadata={
    #         "path": request.url.path,
    #         "method": request.method,
    #         "headers": dict(request.headers),
    #     },
    # )

    # await guardar_log(log)

    return respuesta_error_estandar(
        detalle="La ruta solicitada no existe o no está disponible.",
        status_code=404,
        error_type="RutaNoEncontrada",
    )

# ==========================================================
# 🏁 Endpoint raíz de verificación
# ==========================================================
@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    """
    Endpoint base del sistema bancario.
    Devuelve un mensaje simple para verificar que la API está corriendo.
    """
    return {"msg": "✅ Sistema Bancario Iniciado correctamente"}
