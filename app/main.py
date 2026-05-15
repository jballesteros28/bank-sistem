from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apps.admin.routes import router as admin_router
from app.apps.auditoria.routes import router as auditoria_router
from app.apps.auth.routes import router as auth_router
from app.apps.movimientos.routes import router as movimientos_router
from app.apps.notificaciones.routes import router as notificaciones_router
from app.apps.onboarding.routes import router as onboarding_router
from app.apps.organizaciones.routes import router as organizaciones_router
from app.apps.usuarios.routes import router as usuarios_router
from app.apps.wallets.routes import router as wallets_router
from app.core.api import API_V1_PREFIX
from app.core.config import settings
from app.middlewares.error_handler import register_exception_handlers
from app.middlewares.request_logger import RequestLoggerMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0-alpha",
    description="API multi-tenant para Wallet SaaS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
app.include_router(usuarios_router, prefix=API_V1_PREFIX)
app.include_router(wallets_router, prefix=API_V1_PREFIX)
app.include_router(movimientos_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(auditoria_router, prefix=API_V1_PREFIX)
app.include_router(notificaciones_router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME}

