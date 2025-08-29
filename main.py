from fastapi import FastAPI, Request
from app.auth import routes as auth_routes
from app.usuarios import routes as usuarios_routes 
from app.cuentas import routes as cuentas_routes
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.excepciones import (manejar_errores_validacion,
                              manejar_http_exception,
                              manejar_error_general,
                              manejar_error_sqlalchemy,
                              manejar_cuenta_congelada,
                              respuesta_error_estandar,
                              CuentaCongeladaError,
                              SaldoInsuficienteError
                              )
from services.log_service import guardar_log
from services.transaccion_service import manejar_saldo_insuficiente
from models.log import LogMongo

app = FastAPI(title="Sistema Bancario")

# 🔐 Manejadores de errores globales
app.add_exception_handler(RequestValidationError, manejar_errores_validacion)
app.add_exception_handler(StarletteHTTPException, manejar_http_exception)
app.add_exception_handler(SQLAlchemyError, manejar_error_sqlalchemy)
app.add_exception_handler(CuentaCongeladaError, manejar_cuenta_congelada)
app.add_exception_handler(Exception, manejar_error_general)
app.add_exception_handler(SaldoInsuficienteError, manejar_saldo_insuficiente)

# Registrar los routers
app.include_router(auth_routes.router)
app.include_router(usuarios_routes.router) 
app.include_router(cuentas_routes.router)

@app.exception_handler(404)
async def ruta_no_encontrada(request: Request, exc):
    log = LogMongo(
        evento="RutaNoEncontrada",
        mensaje=f"Intento de acceder a {request.url}",
        nivel="INFO",
        ip=request.client.host
    )
    await guardar_log(log)

    return respuesta_error_estandar(
        detalle="La ruta solicitada no existe.",
        status_code=404,
        error_type="RutaNoEncontrada"
    )



@app.get("/")
def root():
    return {"msg": "Sistema Bancario Iniciado"}
