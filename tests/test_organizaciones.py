from __future__ import annotations

from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.seguridad import crear_token
from database.db_postgres import SessionLocal
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario


SEED_ADMIN_EMAIL = "superadmin@sistemabancario.com"


def _token_para_usuario(email: str) -> str:
    db: Session = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None, f"Usuario {email} no encontrado en seed"
        payload = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "organizacion_id": str(usuario.organizacion_id) if usuario.organizacion_id else None,
        }
        return crear_token(payload)
    finally:
        db.close()


def _headers_admin() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_para_usuario(SEED_ADMIN_EMAIL)}"}


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_crear_organizacion_ok(client: TestClient) -> None:
    slug = f"org-{uuid4().hex[:8]}"
    payload = {
        "nombre": "Organizacion QA",
        "slug": slug,
        "email_contacto": f"{slug}@example.com",
    }

    r = client.post("/organizaciones", headers=_headers_admin(), json=payload)

    assert r.status_code == status.HTTP_201_CREATED, r.text
    data = _data(r)
    assert data["slug"] == slug
    assert data["estado"] == "activa"


def test_no_permite_slug_duplicado(client: TestClient) -> None:
    slug = f"org-duplicada-{uuid4().hex[:8]}"
    payload = {
        "nombre": "Organizacion Duplicada",
        "slug": slug,
        "email_contacto": f"{slug}@example.com",
    }

    r1 = client.post("/organizaciones", headers=_headers_admin(), json=payload)
    assert r1.status_code == status.HTTP_201_CREATED, r1.text

    r2 = client.post("/organizaciones", headers=_headers_admin(), json=payload)
    assert r2.status_code == status.HTTP_400_BAD_REQUEST
    assert "slug" in r2.json()["detail"].lower()


def test_listar_organizaciones(client: TestClient) -> None:
    r = client.get("/organizaciones", headers=_headers_admin())

    assert r.status_code == status.HTTP_200_OK, r.text
    data = _data(r)
    assert isinstance(data, list)
    assert any(org["slug"] == "organizacion-demo" for org in data)


def test_cambiar_estado_organizacion(client: TestClient) -> None:
    slug = f"org-estado-{uuid4().hex[:8]}"
    payload = {
        "nombre": "Organizacion Estado",
        "slug": slug,
        "email_contacto": f"{slug}@example.com",
    }
    creada = client.post("/organizaciones", headers=_headers_admin(), json=payload)
    assert creada.status_code == status.HTTP_201_CREATED, creada.text
    organizacion_id = _data(creada)["id"]

    r = client.patch(
        f"/organizaciones/{organizacion_id}/estado",
        headers=_headers_admin(),
        json={"estado": "suspendida"},
    )

    assert r.status_code == status.HTTP_200_OK, r.text
    assert _data(r)["estado"] == "suspendida"


def test_registro_usuario_asociado_a_organizacion_demo(client: TestClient) -> None:
    email = f"usuario-{uuid4().hex[:8]}@example.com"
    payload = {"nombre": "Usuario Org", "email": email, "password": "Password123!"}

    r = client.post("/auth/register", json=payload)
    assert r.status_code == status.HTTP_201_CREATED, r.text

    db: Session = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        assert usuario is not None
        assert usuario.organizacion_id is not None
        organizacion = db.get(Organizacion, usuario.organizacion_id)
        assert organizacion is not None
        assert organizacion.slug == "organizacion-demo"
    finally:
        db.close()


def test_crear_cuenta_asociada_a_organizacion(client: TestClient) -> None:
    email = f"cuenta-org-{uuid4().hex[:8]}@example.com"
    payload = {"nombre": "Usuario Cuenta Org", "email": email, "password": "Password123!"}
    r_registro = client.post("/auth/register", json=payload)
    assert r_registro.status_code == status.HTTP_201_CREATED, r_registro.text

    token = _token_para_usuario(email)
    headers = {"Authorization": f"Bearer {token}"}
    r_cuenta = client.post("/cuentas/", headers=headers, json={"tipo": "corriente"})
    assert r_cuenta.status_code == status.HTTP_201_CREATED, r_cuenta.text

    cuenta_id = r_cuenta.json()["id"]
    db: Session = SessionLocal()
    try:
        cuenta = db.get(Cuenta, cuenta_id)
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        assert cuenta is not None
        assert usuario is not None
        assert cuenta.organizacion_id == usuario.organizacion_id
    finally:
        db.close()
