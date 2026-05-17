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
    operativa = "operativa"
    caja = "caja"
    recompensas = "recompensas"


class OwnerTypeWallet(StrEnum):
    usuario = "usuario"
    organizacion = "organizacion"


class EstadoWallet(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    congelada = "congelada"
    cerrada = "cerrada"


class MonedaWallet(StrEnum):
    ARS = "ARS"
    USD = "USD"
    PUNTOS = "PUNTOS"


class TipoRecompensa(StrEnum):
    cashback = "cashback"
    puntos = "puntos"
    credito_tienda = "credito_tienda"


class EstadoReglaRecompensa(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    pausada = "pausada"


class MonedaRecompensa(StrEnum):
    ARS = "ARS"
    USD = "USD"
    PUNTOS = "PUNTOS"


class TipoMovimiento(StrEnum):
    deposito = "deposito"
    retiro = "retiro"
    transferencia = "transferencia"
    pago = "pago"
    cashback = "cashback"
    credito_tienda = "credito_tienda"
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
    recompensa_aplicada = "recompensa_aplicada"
    movimiento_ajuste_admin = "movimiento_ajuste_admin"
    movimiento_reversa = "movimiento_reversa"
    wallet_congelada = "wallet_congelada"
    wallet_organizacion_creada = "wallet_organizacion_creada"
    pago_organizacion_realizado = "pago_organizacion_realizado"
    pago_organizacion_recibido = "pago_organizacion_recibido"
    organizacion_suspendida = "organizacion_suspendida"
    seguridad = "seguridad"


class CanalNotificacion(StrEnum):
    interna = "interna"
    email = "email"


class EstadoNotificacion(StrEnum):
    queued = "queued"
    sent = "sent"
    failed = "failed"
