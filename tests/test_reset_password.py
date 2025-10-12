# tests/test_reset_password.py
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from database.db_postgres import SessionLocal
from models.reset_password import ResetPasswordToken
from models.usuario import Usuario
from datetime import datetime, timedelta


# 🔎 Helper para obtener último token de un usuario en la DB de test
def obtener_token(email: str) -> ResetPasswordToken:
    db: Session = SessionLocal()
    try:
        token: ResetPasswordToken | None = (
            db.query(ResetPasswordToken)
            .join(ResetPasswordToken.usuario)
            .filter(ResetPasswordToken.usuario.has(Usuario.email == email))
            .order_by(ResetPasswordToken.id.desc())
            .first()
        )
        assert token is not None, f"No se generó token para {email}"
        return token
    finally:
        db.close()


# ==========================================================
# ✅ Grupo 1: HAPPY PATH
# ==========================================================
def test_flujo_reset_password_happy_path(client: TestClient) -> None:
    email: str = "emisor@test.com"

    # 1) Solicitar reset
    r1 = client.post("/auth/forgot-password", json={"email": email})
    assert r1.status_code == 200
    token: ResetPasswordToken = obtener_token(email)

    # 2) Validar token
    r2 = client.post("/auth/validate-reset", json={"email": email, "codigo": token.token})
    assert r2.status_code == 200
    assert r2.json()["msg"] == "El código es válido"

    # 3) Confirmar reset con nueva password
    nueva_pass: str = "NuevaPass123!"
    r3 = client.post(
        "/auth/reset-password",
        json={"email": email, "codigo": token.token, "nueva_password": nueva_pass}
    )
    assert r3.status_code == 200
    assert "restablecida" in r3.json()["msg"]

    # 4) Login con nueva password funciona
    r4 = client.post("/auth/login", json={"email": email, "password": nueva_pass})
    assert r4.status_code == 200
    assert "access_token" in r4.json()

    # 4b) Login con vieja password falla
    r5 = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    assert r5.status_code == 400


# ==========================================================
# 🚫 Grupo 2: CASOS NEGATIVOS
# ==========================================================
def test_reset_password_email_inexistente(client: TestClient) -> None:
    r = client.post("/auth/forgot-password", json={"email": "noexiste@test.com"})
    # Debe devolver 200, pero no generar token
    assert r.status_code == 200


def test_reset_password_token_invalido(client: TestClient) -> None:
    email: str = "emisor@test.com"
    client.post("/auth/forgot-password", json={"email": email})
    r = client.post("/auth/validate-reset", json={"email": email, "codigo": "token-falso"})
    assert r.status_code == 400
    assert "inválido" in r.json()["detail"].lower()


def test_reset_password_token_ya_usado(client: TestClient) -> None:
    email: str = "emisor@test.com"
    client.post("/auth/forgot-password", json={"email": email})
    token: ResetPasswordToken = obtener_token(email)

    # Confirmar reset (marca token como usado)
    client.post(
        "/auth/reset-password",
        json={"email": email, "codigo": token.token, "nueva_password": "OtraPass123!"}
    )

    # Intentar reusar el token
    r = client.post("/auth/validate-reset", json={"email": email, "codigo": token.token})
    assert r.status_code == 400
    assert "utilizado" in r.json()["detail"].lower()


def test_reset_password_token_expirado(client: TestClient) -> None:
    email: str = "emisor@test.com"
    client.post("/auth/forgot-password", json={"email": email})
    token: ResetPasswordToken = obtener_token(email)

    # Forzar expiración en DB
    db: Session = SessionLocal()
    token.expiracion = datetime.now() - timedelta(minutes=1)
    db.add(token)
    db.commit()
    token_value: str = token.token  # 👈 guardar antes de cerrar la sesión
    db.close()

    # Validar token expirado
    r = client.post("/auth/validate-reset", json={"email": email, "codigo": token_value})
    assert r.status_code == 400
    assert "expirado" in r.json()["detail"].lower()


def test_reset_password_token_bloqueado_por_intentos(client: TestClient) -> None:
    email: str = "emisor@test.com"
    client.post("/auth/forgot-password", json={"email": email})
    token: ResetPasswordToken = obtener_token(email)

    # Simular demasiados intentos
    db: Session = SessionLocal()
    token.intentos = 3  # supera el límite configurado
    db.add(token)
    db.commit()
    token_value: str = token.token
    db.close()

    # Validar token → debe estar bloqueado
    r = client.post("/auth/validate-reset", json={"email": email, "codigo": token_value})
    assert r.status_code == 400
    assert "bloqueado" in r.json()["detail"].lower()


def test_reset_password_token_de_otro_usuario(client: TestClient) -> None:
    # 1. Generar token para receptor
    client.post("/auth/forgot-password", json={"email": "receptor@test.com"})
    token_receptor: ResetPasswordToken = obtener_token("receptor@test.com")

    # 2. Intentar usarlo con emisor
    r = client.post("/auth/validate-reset", json={"email": "emisor@test.com", "codigo": token_receptor.token})
    assert r.status_code == 400
    assert "inválido" in r.json()["detail"].lower()
