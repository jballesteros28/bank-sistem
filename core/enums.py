from enum import Enum

# 🔐 Roles de usuario
class RolUsuario(str, Enum):
    cliente = "cliente"
    admin = "admin"
    soporte = "soporte"

# 💳 Tipos de cuenta bancaria
class TipoCuenta(str, Enum):
    ahorro = "ahorro"
    corriente = "corriente"
    sueldo = "sueldo"

# 📌 Estados posibles de una cuenta
class EstadoCuenta(str, Enum):
    activa = "activa"
    inactiva = "inactiva"
    congelada = "congelada"
