from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.apps.auditoria.schemas import AuditLogCreate, AuditLogResponse
from app.apps.auditoria.services import listar_audit_logs, registrar_audit_log
from app.apps.auth.dependencies import get_current_admin
from app.apps.auth.schemas import DatosUsuarioToken
from app.core.database import get_db
from app.shared.responses import ApiResponse, ok


router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("", response_model=ApiResponse[list[AuditLogResponse]])
def get_logs(
    organizacion_id: UUID | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[AuditLogResponse]]:
    return ok(
        listar_audit_logs(current_user, db, organizacion_id, skip, limit),
        "Logs de auditoria obtenidos.",
    )


@router.post("", response_model=ApiResponse[AuditLogResponse], status_code=status.HTTP_201_CREATED)
def post_log(
    datos: AuditLogCreate,
    current_user: DatosUsuarioToken = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AuditLogResponse]:
    if datos.actor_usuario_id is None and datos.actor_api_key_id is None:
        datos.actor_tipo = "usuario"
        datos.actor_usuario_id = current_user.id
    if datos.organizacion_id is None:
        datos.organizacion_id = current_user.organizacion_id
    return ok(registrar_audit_log(datos, db), "Log de auditoria registrado.")
