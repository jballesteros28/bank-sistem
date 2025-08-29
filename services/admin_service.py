from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from schemas.usuario import CambiarRolUsuario
from schemas.usuario import UsuarioOut
from schemas.cuenta import CambiarEstadoCuenta
from schemas.transaccion import TransaccionOut
from models.cuenta import Cuenta
from models.usuario import Usuario
from models.transaccion import Transaccion
from core.enums import EstadoCuenta
from datetime import datetime
from typing import List, Dict

# 👥 Obtener todos los usuarios registrados
def obtener_usuarios(db: Session) -> List[UsuarioOut]:
    usuarios = db.query(Usuario).all()
    return [UsuarioOut.model_validate(u) for u in usuarios]


# 🔄 Cambiar el rol de un usuario existente
def cambiar_rol_usuario(
    usuario_id: int,
    datos: CambiarRolUsuario,
    db: Session
) -> UsuarioOut:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.rol = datos.nuevo_rol
    db.commit()
    db.refresh(usuario)

    return UsuarioOut.model_validate(usuario)



# ❄️ Cambiar el estado de una cuenta (activar / congelar / inactivar)
def cambiar_estado_cuenta(
    cuenta_id: int,
    datos: CambiarEstadoCuenta,
    db: Session
) -> Cuenta:
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()

    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    cuenta.estado = datos.nuevo_estado
    db.commit()
    db.refresh(cuenta)

    return cuenta


# 📈 Reporte de transacciones entre fechas
def reporte_transacciones_por_fecha(
    desde: datetime,
    hasta: datetime,
    db: Session
) -> list[TransaccionOut]:
    transacciones = db.query(Transaccion).filter(
        and_(
            Transaccion.fecha >= desde,
            Transaccion.fecha <= hasta
        )
    ).order_by(Transaccion.fecha.desc()).all()

    return [TransaccionOut.model_validate(t) for t in transacciones]


# 📊 Resumen de cuentas por estado
def resumen_cuentas_por_estado(db: Session) -> Dict[str, int]:
    resultados = db.query(Cuenta.estado, func.count()).group_by(Cuenta.estado).all()

    # Convertimos a diccionario
    resumen = {estado.value: 0 for estado in EstadoCuenta}
    for estado, cantidad in resultados:
        resumen[estado] = cantidad

    return resumen