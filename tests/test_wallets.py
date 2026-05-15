from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.apps.wallets.models import Wallet
from app.shared.enums import EstadoWallet, MonedaWallet, OwnerTypeWallet, RolUsuario, TipoWallet
from tests.conftest import api_data, auth_headers, create_org, create_org_wallet, create_user, create_wallet


def test_crear_y_listar_wallets(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    created = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Ahorro", "tipo": "ahorro", "moneda": "ARS"},
    )
    assert created.status_code == 201, created.text
    assert api_data(created)["alias"] == "Ahorro"
    assert api_data(created)["owner_type"] == "usuario"

    listed = client.get("/api/v1/wallets", headers=auth_headers(owner))
    assert listed.status_code == 200, listed.text
    assert len(api_data(listed)) == 1


def test_wallets_aisladas_por_organizacion(client: TestClient, db_session: Session) -> None:
    org_a = create_org(db_session)
    org_b = create_org(db_session)
    user_a = create_user(db_session, org_a)
    user_b = create_user(db_session, org_b)
    wallet_b = create_wallet(db_session, user_b, saldo=Decimal("10.00"))

    response = client.get(f"/api/v1/wallets/{wallet_b.id}", headers=auth_headers(user_a))

    assert response.status_code == 404


def test_owner_y_admin_pueden_crear_wallet_de_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    admin = create_user(db_session, org, RolUsuario.admin)

    owner_response = client.post(
        "/api/v1/wallets/organizacion",
        headers=auth_headers(owner),
        json={"alias": "Caja central", "tipo": "caja", "moneda": "ARS"},
    )
    admin_response = client.post(
        "/api/v1/wallets/organizacion",
        headers=auth_headers(admin),
        json={"alias": "Operativa USD", "tipo": "operativa", "moneda": "USD"},
    )

    assert owner_response.status_code == 201, owner_response.text
    assert admin_response.status_code == 201, admin_response.text
    assert api_data(owner_response)["owner_type"] == "organizacion"
    assert api_data(owner_response)["usuario_id"] is None
    assert api_data(owner_response)["organizacion_owner_id"] == str(org.id)


def test_cliente_y_soporte_no_pueden_crear_wallet_de_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    cliente = create_user(db_session, org, RolUsuario.cliente)
    soporte = create_user(db_session, org, RolUsuario.soporte)

    for usuario in (cliente, soporte):
        response = client.post(
            "/api/v1/wallets/organizacion",
            headers=auth_headers(usuario),
            json={"alias": "Caja", "tipo": "caja", "moneda": "ARS"},
        )
        assert response.status_code == 403


def test_listar_wallets_de_organizacion_respeta_roles(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    soporte = create_user(db_session, org, RolUsuario.soporte)
    cliente = create_user(db_session, org, RolUsuario.cliente)
    create_org_wallet(db_session, org)

    owner_response = client.get("/api/v1/wallets/organizacion", headers=auth_headers(owner))
    soporte_response = client.get("/api/v1/wallets/organizacion", headers=auth_headers(soporte))
    cliente_response = client.get("/api/v1/wallets/organizacion", headers=auth_headers(cliente))

    assert owner_response.status_code == 200, owner_response.text
    assert soporte_response.status_code == 200, soporte_response.text
    assert cliente_response.status_code == 403
    assert len(api_data(owner_response)) == 1
    assert api_data(soporte_response)[0]["owner_type"] == "organizacion"


def test_owner_puede_obtener_wallet_principal_de_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    wallet = create_org_wallet(db_session, org, es_principal=True)

    response = client.get("/api/v1/wallets/organizacion/principal", headers=auth_headers(owner))

    assert response.status_code == 200, response.text
    assert api_data(response)["id"] == str(wallet.id)
    assert api_data(response)["es_principal"] is True


def test_wallet_de_organizacion_cuenta_dentro_del_limite(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    create_wallet(db_session, owner)
    create_wallet(db_session, owner)

    org_wallet = client.post(
        "/api/v1/wallets/organizacion",
        headers=auth_headers(owner),
        json={"alias": "Empresa", "tipo": "empresa", "moneda": "ARS"},
    )
    assert org_wallet.status_code == 201, org_wallet.text

    extra = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Extra", "tipo": "ahorro", "moneda": "ARS"},
    )
    assert extra.status_code == 403
    assert "Limite de wallets" in extra.json()["detail"]


def test_no_permite_owner_type_invalido(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Invalida", "tipo": "ahorro", "moneda": "ARS", "owner_type": "mixta"},
    )

    assert response.status_code == 422


def test_no_permite_wallet_con_dos_duenos(db_session: Session) -> None:
    org = create_org(db_session)
    user = create_user(db_session, org)
    wallet = Wallet(
        alias="Hibrida",
        tipo=TipoWallet.principal,
        estado=EstadoWallet.activa,
        moneda=MonedaWallet.ARS,
        saldo=Decimal("0.00"),
        es_principal=False,
        owner_type=OwnerTypeWallet.usuario,
        usuario_id=user.id,
        organizacion_owner_id=org.id,
        organizacion_id=org.id,
    )

    db_session.add(wallet)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_no_permite_wallet_sin_dueno_valido(db_session: Session) -> None:
    org = create_org(db_session)
    wallet = Wallet(
        alias="Sin dueno",
        tipo=TipoWallet.empresa,
        estado=EstadoWallet.activa,
        moneda=MonedaWallet.ARS,
        saldo=Decimal("0.00"),
        es_principal=False,
        owner_type=OwnerTypeWallet.organizacion,
        usuario_id=None,
        organizacion_owner_id=None,
        organizacion_id=org.id,
    )

    db_session.add(wallet)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
