from enum import StrEnum


class TipoMovimiento(StrEnum):
    """Tipos de movimiento expuestos por la API SaaS de wallet."""

    deposito = "deposito"
    retiro = "retiro"
    transferencia = "transferencia"
    pago = "pago"
    cashback = "cashback"
    ajuste_admin = "ajuste_admin"
    reversa = "reversa"


class EstadoMovimiento(StrEnum):
    """Estados funcionales del ciclo de vida de un movimiento."""

    pendiente = "pendiente"
    aprobada = "aprobada"
    rechazada = "rechazada"
    cancelada = "cancelada"
    revertida = "revertida"

