from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from core.seguridad import get_current_user
from schemas.auth import DatosUsuarioToken
from schemas.cuenta import CuentaCreate, CuentaOut
from services.cuenta_service import crear_cuenta, obtener_cuentas_usuario
from typing import List
from core.dependencias import get_db

# Crear router específico para cuentas
router = APIRouter(prefix="/cuentas", tags=["Cuentas"])

# 🏦 Ruta: Crear nueva cuenta bancaria para el usuario autenticado
@router.post("/", response_model=CuentaOut, status_code=status.HTTP_201_CREATED)
def crear_nueva_cuenta(
    cuenta_datos: CuentaCreate,
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva cuenta bancaria para el usuario autenticado.
    Máximo permitido: 3 cuentas activas por tipo.
    """
    return crear_cuenta(cuenta_datos, usuario_token.id, db)

# 📋 Ruta: Listar todas las cuentas del usuario autenticado
@router.get("/", response_model=List[CuentaOut], status_code=status.HTTP_200_OK)
def listar_cuentas(
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Devuelve todas las cuentas del usuario autenticado.
    """
    return obtener_cuentas_usuario(usuario_token.id, db)
