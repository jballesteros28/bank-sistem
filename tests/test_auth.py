# tests/test_auth.py
import random
from starlette.testclient import TestClient
from typing import Dict, Any


# 🔧 Helper para generar emails únicos
def generar_email() -> str:
    return f"test{random.randint(1000, 9999)}@example.com"


# ─────────────────────────────────────────────
# 1) Registro exitoso
# ─────────────────────────────────────────────
def test_registro_exitoso(client: TestClient) -> None:
    email: str = generar_email()
    payload: Dict[str, Any] = {"nombre": "Usuario Test", "email": email, "password": "Password123!"}

    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text

    data: Dict[str, Any] = r.json()
    assert data["usuario"]["email"] == email
    assert data["usuario"]["rol"] == "cliente"


# ─────────────────────────────────────────────
# 2) Registro duplicado
# ─────────────────────────────────────────────
def test_registro_duplicado(client: TestClient) -> None:
    email: str = generar_email()
    payload: Dict[str, Any] = {"nombre": "Usuario Test", "email": email, "password": "Password123!"}

    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201, r1.text

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400, r2.text  # "El email ya está registrado"


# ─────────────────────────────────────────────
# 3) Login exitoso
# ─────────────────────────────────────────────
def test_login_exitoso(client: TestClient) -> None:
    email: str = generar_email()
    payload: Dict[str, Any] = {"nombre": "Usuario Test", "email": email, "password": "Password123!"}

    r_reg = client.post("/auth/register", json=payload)
    assert r_reg.status_code == 201, r_reg.text

    r_login = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    assert r_login.status_code == 200, r_login.text

    token_data: Dict[str, Any] = r_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


# ─────────────────────────────────────────────
# 4) Login con credenciales inválidas
# ─────────────────────────────────────────────
def test_login_invalido(client: TestClient) -> None:
    email: str = generar_email()
    payload: Dict[str, Any] = {"nombre": "Usuario Test", "email": email, "password": "Password123!"}

    r_reg = client.post("/auth/register", json=payload)
    assert r_reg.status_code == 201, r_reg.text

    r_bad = client.post("/auth/login", json={"email": email, "password": "ClaveIncorrecta!"})
    assert r_bad.status_code == 400, r_bad.text  # "Credenciales inválidas"


# ─────────────────────────────────────────────
# 5) Login bloqueado tras múltiples intentos
# ─────────────────────────────────────────────
def test_login_bloqueado(client: TestClient) -> None:
    email: str = generar_email()
    payload: Dict[str, Any] = {"nombre": "Usuario Test", "email": email, "password": "Password123!"}

    r_reg = client.post("/auth/register", json=payload)
    assert r_reg.status_code == 201, r_reg.text

    bad: Dict[str, str] = {"email": email, "password": "ClaveIncorrecta!"}

    # En tu service: al alcanzar 5 intentos, bloquea por 15'
    for _ in range(5):
        client.post("/auth/login", json=bad)  # devuelven 400

    # 6º intento ya debería estar bloqueado → 403
    r_block = client.post("/auth/login", json=bad)
    assert r_block.status_code == 403, r_block.text
