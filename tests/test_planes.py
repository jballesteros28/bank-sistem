from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.apps.movimientos.models import Movimiento
from app.apps.organizaciones.models import Organizacion
from app.apps.planes.models import Plan
from app.apps.planes.services import asegurar_planes_base, obtener_plan_por_codigo
from app.shared.enums import EstadoMovimiento, MonedaWallet, RolUsuario, TipoMovimiento
from tests.conftest import api_data, auth_headers, create_org, create_user, create_wallet


def _assign_plan(db: Session, org_id: UUID, code: str) -> Plan:
    asegurar_planes_base(db)
    plan = obtener_plan_por_codigo(code, db)
    assert plan is not None
    org = db.get(Organizacion, org_id)
    if org is None:
        raise AssertionError("Organizacion no encontrada.")
    org.plan_id = plan.id
    db.add(org)
    db.commit()
    db.refresh(plan)
    return plan


def test_asegurar_planes_base_crea_planes_iniciales(db_session: Session) -> None:
    planes = asegurar_planes_base(db_session)
    free = obtener_plan_por_codigo("free", db_session)

    assert {plan.codigo for plan in planes} == {"free", "starter", "pro", "enterprise"}
    assert free is not None
    assert free.limite_wallets == 3

    asegurar_planes_base(db_session)
    assert db_session.scalar(select(func.count()).select_from(Plan)) == 4


def test_super_admin_puede_listar_planes(client: TestClient, db_session: Session) -> None:
    super_admin = create_user(db_session, None, RolUsuario.super_admin)

    response = client.get("/api/v1/planes", headers=auth_headers(super_admin))

    assert response.status_code == 200, response.text
    assert {plan["codigo"] for plan in api_data(response)} == {"free", "starter", "pro", "enterprise"}


def test_owner_puede_ver_plan_actual(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)

    response = client.get("/api/v1/planes/organizacion/actual", headers=auth_headers(owner))

    assert response.status_code == 200, response.text
    data = api_data(response)
    assert data["organizacion_id"] == str(org.id)
    assert data["plan"]["codigo"] == "free"


def test_admin_comun_no_puede_crear_plan(client: TestClient, db_session: Session) -> None:
    admin = create_user(db_session, create_org(db_session), RolUsuario.admin)

    response = client.post(
        "/api/v1/planes",
        headers=auth_headers(admin),
        json={"nombre": "Growth", "codigo": "growth", "precio_mensual": "29.00"},
    )

    assert response.status_code == 403


def test_super_admin_puede_cambiar_plan_de_organizacion(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    super_admin = create_user(db_session, None, RolUsuario.super_admin)
    asegurar_planes_base(db_session)
    pro = obtener_plan_por_codigo("pro", db_session)
    assert pro is not None

    response = client.patch(
        f"/api/v1/planes/organizaciones/{org.id}/cambiar-plan",
        headers=auth_headers(super_admin),
        json={"plan_id": str(pro.id)},
    )

    assert response.status_code == 200, response.text
    assert api_data(response)["plan"]["codigo"] == "pro"
    db_session.refresh(org)
    assert org.plan_id == pro.id


def test_no_se_puede_asignar_plan_inactivo(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    super_admin = create_user(db_session, None, RolUsuario.super_admin)
    plan = Plan(
        nombre="Legacy",
        codigo="legacy",
        precio_mensual=Decimal("0.00"),
        activo=False,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    response = client.patch(
        f"/api/v1/planes/organizaciones/{org.id}/cambiar-plan",
        headers=auth_headers(super_admin),
        json={"plan_id": str(plan.id)},
    )

    assert response.status_code == 400


def test_free_bloquea_wallets_al_superar_limite(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    for _ in range(3):
        create_wallet(db_session, owner)

    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Extra", "tipo": "principal", "moneda": "ARS"},
    )

    assert response.status_code == 403
    assert "Limite de wallets" in response.json()["detail"]


def test_free_bloquea_movimientos_al_superar_limite_mensual(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    admin = create_user(db_session, org, RolUsuario.admin)
    user = create_user(db_session, org)
    wallet = create_wallet(db_session, user)
    free = _assign_plan(db_session, org.id, "free")
    free.limite_movimientos_mes = 1
    db_session.add(free)
    db_session.add(
        Movimiento(
            wallet_origen_id=None,
            wallet_destino_id=wallet.id,
            organizacion_id=org.id,
            monto=Decimal("1.00"),
            moneda=MonedaWallet.ARS,
            tipo=TipoMovimiento.deposito,
            estado=EstadoMovimiento.aprobada,
            es_reversa=False,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/movimientos/deposito",
        headers=auth_headers(admin),
        json={"wallet_destino_id": str(wallet.id), "monto": "1.00"},
    )

    assert response.status_code == 403
    assert "Limite de movimientos mensuales" in response.json()["detail"]


def test_free_bloquea_usuarios_al_superar_limite(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    for _ in range(9):
        create_user(db_session, org)

    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers(owner),
        json={"nombre": "Usuario Extra", "email": "extra@example.com", "password": "Password123!", "rol": "cliente"},
    )

    assert response.status_code == 403
    assert "Limite de usuarios" in response.json()["detail"]


def test_enterprise_permite_limites_ilimitados(client: TestClient, db_session: Session) -> None:
    org = create_org(db_session)
    owner = create_user(db_session, org, RolUsuario.owner)
    _assign_plan(db_session, org.id, "enterprise")
    for _ in range(5):
        create_wallet(db_session, owner)

    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers(owner),
        json={"alias": "Sin limite", "tipo": "principal", "moneda": "ARS"},
    )

    assert response.status_code == 201, response.text
    assert api_data(response)["alias"] == "Sin limite"
