from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import api_data, create_org, onboarding_payload


def test_registro_login_y_usuario_actual(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session, slug="registro-auth")

    registro = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Cliente Auth",
            "email": "cliente-auth@example.com",
            "password": "Password123!",
            "organizacion_slug": org.slug,
        },
    )
    assert registro.status_code == 201, registro.text
    assert api_data(registro)["rol"] == "cliente"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "cliente-auth@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert api_data(me)["email"] == "cliente-auth@example.com"


def test_login_owner_creado_por_onboarding(client: TestClient) -> None:
    payload = onboarding_payload()
    creado = client.post("/api/v1/onboarding/registro-organizacion", json=payload)
    assert creado.status_code == 201, creado.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["owner"]["email"], "password": payload["owner"]["password"]},
    )
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "bearer"

