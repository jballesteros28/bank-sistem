from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_user
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken
from schemas.transaccion import TransaccionCreate, TransaccionOut
from services.transaccion_service import obtener_historial_usuario, realizar_transferencia


router = APIRouter(prefix="/transacciones", tags=["Transacciones"])


@router.post("/", response_model=TransaccionOut, status_code=status.HTTP_201_CREATED)
def transferir_dinero(
    datos: TransaccionCreate,
    cuenta_origen_id: int,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> TransaccionOut:
    """Realiza una transferencia dentro de la organizacion del usuario."""
    return realizar_transferencia(
        usuario_id=usuario.id,
        cuenta_origen_id=cuenta_origen_id,
        organizacion_id=organizacion.id,
        datos_transaccion=datos,
        db=db,
        background_tasks=background_task,
    )


@router.get("/historial", response_model=list[TransaccionOut])
def ver_historial(
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> list[TransaccionOut]:
    """Devuelve el historial limitado a la organizacion del usuario."""
    return obtener_historial_usuario(usuario.id, organizacion.id, db)
