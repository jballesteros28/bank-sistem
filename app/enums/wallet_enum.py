from enum import StrEnum


class TipoWallet(StrEnum):
    """Tipos funcionales de wallet ofrecidos por el modulo SaaS."""

    principal = "principal"
    ahorro = "ahorro"
    recompensas = "recompensas"
    empresa = "empresa"


class EstadoWallet(StrEnum):
    """Estados operativos de una wallet digital."""

    activa = "activa"
    inactiva = "inactiva"
    congelada = "congelada"
    cerrada = "cerrada"


class MonedaWallet(StrEnum):
    """Monedas y unidades soportadas por las wallets."""

    ARS = "ARS"
    USD = "USD"
    USDT = "USDT"
    PUNTOS = "PUNTOS"

