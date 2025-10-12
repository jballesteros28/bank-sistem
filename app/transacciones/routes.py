from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from schemas.transaccion import TransaccionCreate, TransaccionOut
from services.transaccion_service import realizar_transferencia
from core.seguridad import get_current_user
from core.dependencias import get_db
from schemas.auth import DatosUsuarioToken
from typing import List
from services.transaccion_service import obtener_historial_usuario

router = APIRouter(
    prefix="/transacciones",
    tags=["Transacciones"]
)

# 🔄 Endpoint para realizar una transferencia entre cuentas
@router.post("/", response_model=TransaccionOut, status_code=status.HTTP_201_CREATED)
def transferir_dinero(
    datos: TransaccionCreate,                      # 📥 Datos enviados por el usuario
    cuenta_origen_id: int,                         # 🆔 ID de la cuenta origen (en query o body)
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),                 # 🔌 Conexión a la base de datos
    usuario: DatosUsuarioToken = Depends(get_current_user),  # 🔐 Usuario autenticado
):
    """
    Realiza una transferencia entre la cuenta origen del usuario y otra cuenta de destino.
    """
    return realizar_transferencia(
        usuario_id=usuario.id,
        cuenta_origen_id=cuenta_origen_id,
        datos_transaccion=datos,
        db=db,
        background_tasks=background_task,
        
    )


# 📋 Ruta: Historial de transacciones del usuario
@router.get("/historial", response_model=List[TransaccionOut])
def ver_historial(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user)
):
    """
    Devuelve el historial de transacciones realizadas por el usuario autenticado.
    """
    return obtener_historial_usuario(usuario.id, db)