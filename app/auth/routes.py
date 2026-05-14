from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, Dict

# ── Schemas principales ───────────────────────
from schemas.auth import RegistroUsuario, LoginUsuario, TokenRespuesta
from schemas.reset_password import (
    ForgotPasswordRequest,
    ValidateResetRequest,
    ResetPasswordConfirm,
    ResetPasswordResponse,
)

# ── Services ──────────────────────────────────
from services.auth_service import registrar_usuario, login_usuario
from services import reset_password_service
# ── Dependencias ──────────────────────────────
from core.dependencias import get_db

# ── Router ────────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ══════════════════════════════════════════════
# 📌 Registro de usuario
# ══════════════════════════════════════════════
@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(
    datos: RegistroUsuario,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Registra un nuevo usuario en el sistema.
    El envío de correo de bienvenida se maneja en el service.
    """
    usuario = registrar_usuario(datos, db, background_tasks)
    

    return {
        "msg": "Usuario registrado exitosamente",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
        },
    }


# ══════════════════════════════════════════════
# 📌 Login y retorno de JWT
# ══════════════════════════════════════════════
@router.post("/login", response_model=TokenRespuesta)
async def login(
    data: LoginUsuario,
    request: Request,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TokenRespuesta:
    """
    Realiza login de usuario.
    Si las credenciales son válidas, devuelve un token JWT.
    """
    return await login_usuario(data, request, db, background_task)


# ══════════════════════════════════════════════
# 📌 Reset Password - Solicitar código
# ══════════════════════════════════════════════
@router.post("/forgot-password", response_model=ResetPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """
    Genera un token de recuperación y lo envía al correo del usuario.
    """
    await reset_password_service.solicitar_reset(payload.email, db, background_tasks)
    return ResetPasswordResponse(msg="Se ha enviado un código de recuperación a tu correo")


# ══════════════════════════════════════════════
# 📌 Reset Password - Validar código
# ══════════════════════════════════════════════
@router.post("/validate-reset", response_model=ResetPasswordResponse)
async def validate_reset(
    payload: ValidateResetRequest,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """
    Verifica que el código de recuperación sea válido y no esté vencido.
    """
    await reset_password_service.validar_reset(payload.email, payload.codigo, db)
    return ResetPasswordResponse(msg="El código es válido")


# ══════════════════════════════════════════════
# 📌 Reset Password - Confirmar nueva contraseña
# ══════════════════════════════════════════════
@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordConfirm,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """
    Permite al usuario restablecer su contraseña usando un código válido.
    """
    await reset_password_service.confirmar_reset(
        payload.email, payload.codigo, payload.nueva_password, db,background_task
    )
    return ResetPasswordResponse(msg="Tu contraseña ha sido restablecida exitosamente")
