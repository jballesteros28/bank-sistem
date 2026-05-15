from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.planes.services import asegurar_planes_base, obtener_plan_por_codigo
from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user


def _assign_plan(db: Session, org: Organizacion, code: str) -> Plan:
    asegurar_planes_base(db)
    plan = obtener_plan_por_codigo(code, db)
    assert plan is not None
    org.plan_id = plan.id
    db.add(org)
    db.commit()
    db.refresh(org)
    db.refresh(plan)
    return plan


def test_owner_puede_ver_branding_de_su_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.get("/api/v1/organizaciones/me/branding", headers=auth_headers(owner))

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert data["id"] == str(org.id)
    assert data["moneda_default"] == "ARS"
    assert data["timezone"] == "America/Argentina/Buenos_Aires"
    assert data["permite_white_label_activo"] is False


def test_owner_puede_actualizar_nombre_comercial_y_colores(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={
            "nombre_comercial": "Marca Norte",
            "color_primario": "#1A2B3C",
            "color_secundario": "#abc",
            "subdominio": "marca-norte",
        },
    )

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert data["nombre_comercial"] == "Marca Norte"
    assert data["color_primario"] == "#1A2B3C"
    assert data["color_secundario"] == "#abc"
    assert data["subdominio"] == "marca-norte"


def test_color_invalido_falla(client: TestClient, db_session: Session) -> None:
    owner = create_user(db_session, create_org(db_session), RolUsuario.owner)

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={"color_primario": "azul"},
    )

    assert response.status_code == 422


def test_subdominio_duplicado_falla(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner = create_user(db_session, org_a, RolUsuario.owner)
    org_b.subdominio = "marca"
    db_session.add(org_b)
    db_session.commit()

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={"subdominio": "marca"},
    )

    assert response.status_code == 400


def test_dominio_personalizado_duplicado_falla(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner = create_user(db_session, org_a, RolUsuario.owner)
    org_b.dominio_personalizado = "wallet.example.com"
    db_session.add(org_b)
    db_session.commit()

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={"dominio_personalizado": "wallet.example.com"},
    )

    assert response.status_code == 400


def test_owner_free_no_puede_activar_white_label(client: TestClient, db_session: Session) -> None:
    owner = create_user(db_session, create_org(db_session), RolUsuario.owner)

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={"permite_white_label_activo": True},
    )

    assert response.status_code == 403


def test_owner_free_no_puede_configurar_dominio_personalizado(client: TestClient, db_session: Session) -> None:
    owner = create_user(db_session, create_org(db_session), RolUsuario.owner)

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={"dominio_personalizado": "free.example.com"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize("plan_code", ["pro", "enterprise"])
def test_organizacion_con_plan_white_label_puede_activar_branding_avanzado(
    client: TestClient,
    db_session: Session,
    plan_code: str,
) -> None:
    org = create_org(db_session)
    _assign_plan(db_session, org, plan_code)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.patch(
        "/api/v1/organizaciones/me/branding",
        headers=auth_headers(owner),
        json={
            "permite_white_label_activo": True,
            "dominio_personalizado": f"{plan_code}.example.com",
        },
    )

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert data["permite_white_label_activo"] is True
    assert data["dominio_personalizado"] == f"{plan_code}.example.com"


def test_owner_no_puede_editar_branding_de_otra_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner = create_user(db_session, org_a, RolUsuario.owner)

    response = client.patch(
        f"/api/v1/organizaciones/{org_b.id}/branding",
        headers=auth_headers(owner),
        json={"nombre_comercial": "Otra marca"},
    )

    assert response.status_code == 403


def test_super_admin_puede_editar_branding_de_cualquier_organizacion(
    client: TestClient,
    db_session: Session,
) -> None:
    org = create_org(db_session)
    super_admin = create_user(db_session, None, RolUsuario.super_admin)

    response = client.patch(
        f"/api/v1/organizaciones/{org.id}/branding",
        headers=auth_headers(super_admin),
        json={"nombre_comercial": "Marca Global", "moneda_default": "usd"},
    )

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert UUID(data["id"]) == org.id
    assert data["nombre_comercial"] == "Marca Global"
    assert data["moneda_default"] == "USD"
