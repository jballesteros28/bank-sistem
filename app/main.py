import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.apps.admin.routes import router as admin_router
from app.apps.auditoria.routes import router as auditoria_router
from app.apps.auth.routes import router as auth_router
from app.apps.ecommerce.routes import ext_router as ecommerce_ext_router
from app.apps.ecommerce.routes import router as ecommerce_router
from app.apps.integraciones.routes import ext_router as integraciones_ext_router
from app.apps.integraciones.routes import router as integraciones_router
from app.apps.movimientos.routes import router as movimientos_router
from app.apps.notificaciones.routes import router as notificaciones_router
from app.apps.onboarding.routes import router as onboarding_router
from app.apps.organizaciones.routes import router as organizaciones_router
from app.apps.planes.routes import router as planes_router
from app.apps.recompensas.routes import router as recompensas_router
from app.apps.usuarios.routes import router as usuarios_router
from app.apps.wallets.routes import router as wallets_router
from app.core import database as database_module
from app.core.api import API_V1_PREFIX
from app.core.config import settings
from app.core.logging import configure_logging
from app.middlewares.error_handler import register_exception_handlers
from app.middlewares.request_logger import RequestLoggerMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description=(
        "API multi-tenant para Wallet SaaS. Incluye configuracion de branding "
        "y preparacion white-label por organizacion."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggerMiddleware)
register_exception_handlers(app)

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(onboarding_router, prefix=API_V1_PREFIX)
app.include_router(organizaciones_router, prefix=API_V1_PREFIX)
app.include_router(planes_router, prefix=API_V1_PREFIX)
app.include_router(recompensas_router, prefix=API_V1_PREFIX)
app.include_router(usuarios_router, prefix=API_V1_PREFIX)
app.include_router(wallets_router, prefix=API_V1_PREFIX)
app.include_router(movimientos_router, prefix=API_V1_PREFIX)
app.include_router(integraciones_router, prefix=API_V1_PREFIX)
app.include_router(integraciones_ext_router, prefix=API_V1_PREFIX)
app.include_router(ecommerce_router, prefix=API_V1_PREFIX)
app.include_router(ecommerce_ext_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(auditoria_router, prefix=API_V1_PREFIX)
app.include_router(notificaciones_router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/ready", tags=["Health"], response_model=None)
def ready() -> dict[str, object] | JSONResponse:
    try:
        with database_module.SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Readiness database check failed", exc_info=settings.DEBUG)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": settings.APP_NAME,
                "checks": {"database": "error"},
            },
        )
    return {
        "status": "ready",
        "service": settings.APP_NAME,
        "checks": {"database": "ok"},
    }
