# app/cuentas/routes.py
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from core.seguridad import get_current_user
from schemas.auth import DatosUsuarioToken
from schemas.cuenta import CuentaCreate, CuentaOut
from services.cuenta_service import (
    crear_cuenta,
    obtener_cuentas_usuario,
    obtener_cuenta_por_id,
)
from typing import List
from core.dependencias import get_db

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


# 🏦 Crear nueva cuenta bancaria
@router.post("/", response_model=CuentaOut, status_code=status.HTTP_201_CREATED)
def crear_nueva_cuenta(
    cuenta_datos: CuentaCreate,
    background_task: BackgroundTasks,
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crea una nueva cuenta bancaria para el usuario autenticado.
    - Solo se permite **1 cuenta por tipo** (ahorro, corriente, etc.).
    """
    return crear_cuenta(cuenta_datos, usuario_token.id, db, background_task)


# 📋 Listar todas las cuentas del usuario autenticado
@router.get("/", response_model=List[CuentaOut], status_code=status.HTTP_200_OK)
def listar_cuentas(
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Devuelve todas las cuentas del usuario autenticado.
    """
    return obtener_cuentas_usuario(usuario_token.id, db)


# 📌 Consultar una cuenta específica por ID
@router.get("/{cuenta_id}", response_model=CuentaOut, status_code=status.HTTP_200_OK)
def obtener_cuenta(
    cuenta_id: int,
    usuario_token: DatosUsuarioToken = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Devuelve una cuenta específica del usuario autenticado.
    """
    return obtener_cuenta_por_id(cuenta_id, usuario_token.id, db)
