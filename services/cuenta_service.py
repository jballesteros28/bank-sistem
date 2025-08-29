from sqlalchemy.orm import Session
from models.cuenta import Cuenta
from schemas.cuenta import CuentaCreate, CuentaOut
from fastapi import HTTPException, status
from core.enums import EstadoCuenta, TipoCuenta
from typing import List
import random

# 🧾 Función para generar un número de cuenta único (simple para desarrollo)
def generar_numero_cuenta() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(10))

# 🏦 Crear una nueva cuenta para el usuario autenticado
def crear_cuenta(cuenta_datos: CuentaCreate, usuario_id: int, db: Session) -> CuentaOut:
    # Validar que el usuario no tenga más de 3 cuentas del mismo tipo (opcional)
    cuentas_existentes = db.query(Cuenta).filter(
        Cuenta.usuario_id == usuario_id,
        Cuenta.tipo == cuenta_datos.tipo,
        Cuenta.estado != EstadoCuenta.inactiva  # Podés ajustar lógica
    ).count()

    if cuentas_existentes >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya tienes 3 cuentas activas de tipo '{cuenta_datos.tipo.value}'"
        )

    # Crear nueva cuenta
    nueva_cuenta = Cuenta(
        numero=generar_numero_cuenta(),
        tipo=cuenta_datos.tipo,
        saldo=0.0,
        estado=EstadoCuenta.activa,
        usuario_id=usuario_id
    )

    db.add(nueva_cuenta)
    db.commit()
    db.refresh(nueva_cuenta)

    # Devolver en formato validado
    return CuentaOut.model_validate(nueva_cuenta)

# 📂 Obtener todas las cuentas del usuario autenticado
def obtener_cuentas_usuario(usuario_id: int, db: Session) -> List[CuentaOut]:
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == usuario_id).all()

    if not cuentas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene cuentas registradas"
        )

    return [CuentaOut.model_validate(cuenta) for cuenta in cuentas]
