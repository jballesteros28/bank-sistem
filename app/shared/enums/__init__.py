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
    bienvenida = "bienvenida"
    movimiento = "movimiento"
    seguridad = "seguridad"
    generica = "generica"


class EstadoNotificacion(StrEnum):
    queued = "queued"
    sent = "sent"
    failed = "failed"

