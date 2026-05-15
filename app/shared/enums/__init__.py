from enum import StrEnum


class RolUsuario(StrEnum):
    cliente = "cliente"
    admin = "admin"
    owner = "owner"
    soporte = "soporte"
    super_admin = "super_admin"


class EstadoOrganizacion(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    suspendida = "suspendida"


class TipoWallet(StrEnum):
    principal = "principal"
    ahorro = "ahorro"
    empresa = "empresa"
    recompensas = "recompensas"


class EstadoWallet(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    congelada = "congelada"
    cerrada = "cerrada"


class MonedaWallet(StrEnum):
    ARS = "ARS"
    USD = "USD"
    PUNTOS = "PUNTOS"


class TipoMovimiento(StrEnum):
    deposito = "deposito"
    retiro = "retiro"
    transferencia = "transferencia"
    pago = "pago"
    cashback = "cashback"
    ajuste_admin = "ajuste_admin"
    reversa = "reversa"


class EstadoMovimiento(StrEnum):
    aprobada = "aprobada"
    pendiente = "pendiente"
    rechazada = "rechazada"
    cancelada = "cancelada"
    revertida = "revertida"


class TipoNotificacion(StrEnum):
    onboarding_exitoso = "onboarding_exitoso"
    wallet_creada = "wallet_creada"
    movimiento_deposito = "movimiento_deposito"
    movimiento_retiro = "movimiento_retiro"
    movimiento_transferencia = "movimiento_transferencia"
    movimiento_pago = "movimiento_pago"
    movimiento_cashback = "movimiento_cashback"
    movimiento_ajuste_admin = "movimiento_ajuste_admin"
    movimiento_reversa = "movimiento_reversa"
    wallet_congelada = "wallet_congelada"
    organizacion_suspendida = "organizacion_suspendida"
    seguridad = "seguridad"


class CanalNotificacion(StrEnum):
    interna = "interna"
    email = "email"


class EstadoNotificacion(StrEnum):
    queued = "queued"
    sent = "sent"
    failed = "failed"
