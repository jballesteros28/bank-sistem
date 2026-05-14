from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencias import get_db
from core.seguridad import get_current_user
from dependencies.organizacion_dependencies import get_current_organizacion
from models.organizacion import Organizacion
from schemas.auth import DatosUsuarioToken
from schemas.transaccion import TransaccionCreate, TransaccionOut
from services.transaccion_service import obtener_historial_usuario, realizar_transferencia


router = APIRouter(prefix="/transacciones", tags=["Legacy - Transacciones"], deprecated=True)


@router.post("/", response_model=TransaccionOut, status_code=status.HTTP_201_CREATED)
def transferir_dinero(
    datos: TransaccionCreate,
    background_task: BackgroundTasks,
    cuenta_origen_id: int | None = Query(default=None, gt=0),
    wallet_origen_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    usuario: DatosUsuarioToken = Depends(get_current_user),
    organizacion: Organizacion = Depends(get_current_organizacion),
) -> TransaccionOut:
    """Realiza una transferencia dentro de la organizacion del usuario."""
    origen_id = cuenta_origen_id or wallet_origen_id
    if origen_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe informar cuenta_origen_id o wallet_origen_id.",
        )

    return realizar_transferencia(
        usuario_id=usuario.id,
        cuenta_origen_id=origen_id,
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
