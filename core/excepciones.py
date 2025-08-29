from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import logging
from services.log_service import guardar_log
from models.log import LogMongo

# 📌 Logger para registrar errores en consola (o MongoDB más adelante)
logger = logging.getLogger(__name__)

# ❄️ Excepción personalizada para cuentas congeladas
class CuentaCongeladaError(Exception):
    def __init__(self, mensaje: str="La cuenta está congelada. No se puede operar."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


async def manejar_cuenta_congelada(request: Request, exc: CuentaCongeladaError):
    log = LogMongo(
        evento="OperacionBloqueada",
        mensaje=exc.mensaje,
        nivel="WARNING",
        endpoint=str(request.url),
        ip=request.client.host
    )
    await guardar_log(log)

    return respuesta_error_estandar(
        detalle=exc.mensaje,
        status_code=403,
        error_type="CuentaCongelada"
    )






# 📦 Utilidad para construir una respuesta estándar de error
def respuesta_error_estandar(
    detalle: str,
    status_code: int,
    error_type: str,
    success: bool = False
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "detail": detalle,
            "code": status_code,
            "error_type": error_type
        }
    )
    

# 🚫 Error personalizado: validaciones de Pydantic (campos inválidos)
async def manejar_errores_validacion(request: Request, exc: RequestValidationError):
    errores = [
        {
            "campo": ".".join(str(loc) for loc in error["loc"][1:]),
            "mensaje": error["msg"]
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": "Error de validación de datos",
            "code": 422,
            "error_type": "DatosInvalidos",
            "errores": errores,
            "body": exc.body
        }
    )

# 🚫 Error personalizado: FastAPI HTTPException
async def manejar_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# ❌ Error inesperado del sistema (500)
async def manejar_error_general(request: Request, exc: Exception) -> JSONResponse:
    # Guardar log persistente en MongoDB
    log = LogMongo(
        evento="ErrorInterno",
        mensaje=str(exc),
        nivel="ERROR",
        endpoint=str(request.url),
        ip=request.client.host
    )
    await guardar_log(log)

    return JSONResponse(
        status_code=500,
        content={"detail": "Ha ocurrido un error interno. Por favor, intente más tarde."}
    )

# ❌ Error al acceder a la base de datos
async def manejar_error_sqlalchemy(request: Request, exc: SQLAlchemyError):
    logger.error(f"Error en base de datos: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error de conexión o consulta en la base de datos"}
    )
    
    
# 💸 Excepción personalizada: Saldo insuficiente para realizar la transacción
class SaldoInsuficienteError(Exception):
    def __init__(self, mensaje: str="Saldo insuficiente para realizar la operación."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
