from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from core.enums import EstadoCuenta, RolUsuario, TipoCuenta
from core.seguridad import hash_password
from database.db_postgres import SessionLocal
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario
from services.organizacion_service import obtener_o_crear_organizacion_demo


SEED_PASSWORD = "pass1234"


def _obtener_o_crear_usuario(
    db: Session,
    *,
    nombre: str,
    email: str,
    rol: RolUsuario,
    organizacion: Organizacion,
) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        if usuario.organizacion_id is None:
            # Los seeds existentes quedan asociados al tenant demo.
            usuario.organizacion_id = organizacion.id
            db.add(usuario)
        return usuario

    usuario = Usuario(
        nombre=nombre,
        email=email,
        hashed_password=hash_password(SEED_PASSWORD),
        es_activo=True,
        rol=rol,
        intentos_fallidos=0,
        bloqueado_hasta=None,
        organizacion_id=organizacion.id,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _obtener_o_crear_cuenta(
    db: Session,
    *,
    numero: str,
    usuario: Usuario,
    tipo: TipoCuenta,
    saldo: Decimal,
    organizacion: Organizacion,
) -> Cuenta:
    cuenta = db.query(Cuenta).filter(Cuenta.numero == numero).first()
    if cuenta:
        if cuenta.organizacion_id is None:
            # Las cuentas heredadas quedan asociadas al tenant demo.
            cuenta.organizacion_id = organizacion.id
            db.add(cuenta)
        return cuenta

    cuenta = Cuenta(
        numero=numero,
        tipo=tipo,
        saldo=saldo,
        estado=EstadoCuenta.activa,
        usuario_id=usuario.id,
        organizacion_id=organizacion.id,
    )
    db.add(cuenta)
    db.flush()
    return cuenta


def init_seed() -> None:
    """Crea datos base para desarrollo y tests sin duplicarlos."""
    db = SessionLocal()
    try:
        organizacion = obtener_o_crear_organizacion_demo(db)

        admin = _obtener_o_crear_usuario(
            db,
            nombre="Administrador",
            email="admin@sistemabancario.com",
            rol=RolUsuario.admin,
            organizacion=organizacion,
        )
        emisor = _obtener_o_crear_usuario(
            db,
            nombre="Usuario Emisor",
            email="emisor@test.com",
            rol=RolUsuario.cliente,
            organizacion=organizacion,
        )
        receptor = _obtener_o_crear_usuario(
            db,
            nombre="Usuario Receptor",
            email="receptor@test.com",
            rol=RolUsuario.cliente,
            organizacion=organizacion,
        )

        _obtener_o_crear_cuenta(
            db,
            numero="CTA-100001",
            usuario=emisor,
            tipo=TipoCuenta.ahorro,
            saldo=Decimal("1000.00"),
            organizacion=organizacion,
        )
        _obtener_o_crear_cuenta(
            db,
            numero="CTA-100002",
            usuario=receptor,
            tipo=TipoCuenta.ahorro,
            saldo=Decimal("500.00"),
            organizacion=organizacion,
        )

        # El admin no necesita cuenta para las pruebas actuales, pero queda asociado al tenant.
        db.add(admin)
        db.commit()
    finally:
        db.close()
