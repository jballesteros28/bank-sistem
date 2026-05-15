from pydantic import BaseModel


class AdminResumenResponse(BaseModel):
    organizaciones: int
    usuarios: int
    wallets: int
    movimientos: int

