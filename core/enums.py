# core/enums.py
from enum import StrEnum

# 🔐 Roles de usuario
class RolUsuario(StrEnum):
    cliente = "cliente"
    admin = "admin"
    soporte = "soporte"

# 💳 Tipos de cuenta bancaria
class TipoCuenta(StrEnum):
    ahorro = "ahorro"
    corriente = "corriente"
    sueldo = "sueldo"

# 📌 Estados posibles de una cuenta
class EstadoCuenta(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    congelada = "congelada"

# 📤 Tipos de transacciones
class TipoTransaccion(StrEnum):
    transferencia = "transferencia"
    deposito = "deposito"
    retiro = "retiro"

# ⏳ Estados posibles de una transacción
class EstadoTransaccion(StrEnum):
    completada = "completada"
    fallida = "fallida"
    pendiente = "pendiente"

# 📧 Tipos de notificación
class TipoNotificacion(StrEnum):
    WELCOME = "WELCOME"
    PASSWORD_RESET = "PASSWORD_RESET"
    TRANSFER_CONFIRMATION = "TRANSFER_CONFIRMATION"
    GENERIC = "GENERIC"

# 📧 Estados posibles de una notificación
class EstadoNotificacion(StrEnum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"


# Estados de una organizacion SaaS dentro de la plataforma.
class EstadoOrganizacion(StrEnum):
    activa = "activa"
    inactiva = "inactiva"
    suspendida = "suspendida"
