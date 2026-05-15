from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.shared.enums import RolUsuario
from tests.conftest import api_data, auth_headers, create_org, create_user


def test_owner_admin_operan_solo_en_su_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    owner_a = create_user(db_session, org_a, RolUsuario.owner)
    create_user(db_session, org_b)

    usuarios = client.get("/api/v1/admin/usuarios", headers=auth_headers(owner_a))
    assert usuarios.status_code == 200, usuarios.text
    assert {user["organizacion_id"] for user in api_data(usuarios)} == {str(org_a.id)}

    otra_org = client.get(
        f"/api/v1/admin/usuarios?organizacion_id={org_b.id}",
        headers=auth_headers(owner_a),
    )
    assert otra_org.status_code == 403


def test_super_admin_opera_globalmente(client: TestClient, db_session: Session) -> None:
    create_user(db_session, create_org(db_session), RolUsuario.owner)
    create_user(db_session, create_org(db_session), RolUsuario.admin)
    super_admin = create_user(db_session, None, RolUsuario.super_admin)

    resumen = client.get("/api/v1/admin/resumen", headers=auth_headers(super_admin))
    usuarios = client.get("/api/v1/admin/usuarios", headers=auth_headers(super_admin))

    assert resumen.status_code == 200, resumen.text
    assert api_data(resumen)["organizaciones"] == 2
    assert usuarios.status_code == 200, usuarios.text
    assert len(api_data(usuarios)) == 3

