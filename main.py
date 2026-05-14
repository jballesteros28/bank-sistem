from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.admin import log_routes
from app.admin import routes as admin_routes
from app.auth import routes as auth_routes
from app.cuentas import routes as cuentas_routes
from app.movimientos import routes as movimientos_routes
from app.notificaciones import routes as notificaciones_routes
from app.onboarding import routes as onboarding_routes
from app.organizaciones import routes as organizaciones_routes
from app.transacciones import routes as transacciones_routes
from app.usuarios import routes as usuarios_routes
from app.wallets import routes as wallets_routes
from core.api import API_V1_PREFIX
from core.excepciones import (
    CuentaCongeladaError,
    SaldoInsuficienteError,
    manejar_cuenta_congelada,
    manejar_error_general,
    manejar_error_sqlalchemy,
    manejar_errores_validacion,
    manejar_http_exception,
    respuesta_error_estandar,
)
from middlewares.secure_headers import SecureHeadersMiddleware
from services.log_service import correlation_id_ctx
from services.transaccion_service import manejar_saldo_insuficiente


app = FastAPI(
    title="Wallet SaaS API",
    version="0.5.0",
    description=(
        "API multi-tenant para wallets digitales SaaS con onboarding publico de organizaciones, owners, wallets y movimientos. "
        "La API principal usa /wallets y /movimientos; /cuentas y "
        "/transacciones se mantienen temporalmente como endpoints legacy. "
        f"Prefijo recomendado para la proxima version: {API_V1_PREFIX}."
    ),
    openapi_tags=[
        {"name": "Auth", "description": "Autenticacion y sesiones JWT."},
        {"name": "Onboarding", "description": "Registro publico de organizaciones SaaS con owner y wallet principal."},
        {"name": "Usuarios", "description": "Gestion de usuarios de una organizacion."},
        {"name": "Organizaciones", "description": "Tenants SaaS y su estado operativo."},
        {"name": "Wallets", "description": "API principal de wallets digitales."},
        {"name": "Movimientos", "description": "API principal de movimientos financieros."},
        {"name": "Administración", "description": "Operaciones administrativas de tenant y plataforma."},
        {"name": "Auditoría / Logs", "description": "Consulta de logs y auditoria operativa."},
        {"name": "Notificaciones", "description": "Notificaciones y correos del sistema."},
        {"name": "Legacy - Cuentas", "description": "Endpoints heredados de cuentas bancarias."},
        {"name": "Legacy - Transacciones", "description": "Endpoints heredados de transacciones bancarias."},
        {"name": "General", "description": "Endpoints base de salud y verificacion."},
    ],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Asigna un correlation id unico a cada request."""
    correlation_id = str(uuid.uuid4())
    correlation_id_ctx.set(correlation_id)

    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


origins = [
    "http://localhost:3000",
    "https://mi-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecureHeadersMiddleware)


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Demasiadas solicitudes. Intente mas tarde."},
    )


app.add_exception_handler(RequestValidationError, manejar_errores_validacion)
app.add_exception_handler(StarletteHTTPException, manejar_http_exception)
app.add_exception_handler(SQLAlchemyError, manejar_error_sqlalchemy)
app.add_exception_handler(CuentaCongeladaError, manejar_cuenta_congelada)
app.add_exception_handler(SaldoInsuficienteError, manejar_saldo_insuficiente)
app.add_exception_handler(Exception, manejar_error_general)


app.include_router(auth_routes.router)
app.include_router(onboarding_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(cuentas_routes.router)
app.include_router(wallets_routes.router)
app.include_router(transacciones_routes.router)
app.include_router(movimientos_routes.router)
app.include_router(organizaciones_routes.router)
app.include_router(admin_routes.router)
app.include_router(notificaciones_routes.router)
app.include_router(log_routes.router)


@app.exception_handler(404)
async def ruta_no_encontrada(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detalle_lower = str(exc.detail).lower() if exc.detail else ""

    if "no encontrado" in detalle_lower or "no encontrada" in detalle_lower:
        return respuesta_error_estandar(
            detalle=exc.detail,
            status_code=404,
            error_type="RecursoNoEncontrado",
        )

    return respuesta_error_estandar(
        detalle="La ruta solicitada no existe o no esta disponible.",
        status_code=404,
        error_type="RutaNoEncontrada",
    )


@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    return {"msg": "Wallet SaaS API operativa"}
