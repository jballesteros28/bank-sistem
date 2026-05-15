from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user


def test_super_admin_lista_todas_las_organizaciones(client: TestClient, db_session: Session) -> None:
    create_org(db_session, "org-a")
    create_org(db_session, "org-b")
    super_admin = create_user(db_session, None, RolUsuario.super_admin)

    response = client.get("/api/v1/organizaciones", headers=auth_headers(super_admin))

    assert response.status_code == 200, response.text
    assert {org["slug"] for org in api_data(response)} == {"org-a", "org-b"}


def test_owner_solo_ve_su_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session, "owner-a")
    create_org(db_session, "owner-b")
    owner = create_user(db_session, org_a, RolUsuario.owner)

    response = client.get("/api/v1/organizaciones", headers=auth_headers(owner))

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert len(data) == 1
    assert data[0]["slug"] == "owner-a"

