from fastapi import FastAPI
from core.config import settings
from app.auth import routes as auth_routes

app = FastAPI(title="Sistema Bancario")

app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"msg": "Sistema Bancario Iniciado"}
