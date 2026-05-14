from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.enums import EstadoCuenta, EstadoOrganizacion, RolUsuario, TipoCuenta
from core.seguridad import crear_token, hash_password
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario


def _crear_organizacion(
    db: Session,
    slug: str,
    estado: EstadoOrganizacion = EstadoOrganizacion.activa,
) -> Organizacion:
    organizacion = Organizacion(
        nombre=f"Org {slug}",
        slug=slug,
        email_contacto=f"{slug}@example.com",
        estado=estado,
    )
    db.add(organizacion)
    db.flush()
    return organizacion


def _crear_usuario(
    db: Session,
    organizacion: Organizacion,
    email: str,
    rol: RolUsuario = RolUsuario.cliente,
) -> Usuario:
    usuario = Usuario(
        nombre=email.split("@")[0],
        email=email,
        hashed_password=hash_password("Password123!"),
        es_activo=True,
        rol=rol,
        intentos_fallidos=0,
        bloqueado_hasta=None,
        organizacion_id=organizacion.id,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _crear_cuenta(
    db: Session,
    usuario: Usuario,
    organizacion: Organizacion,
    saldo: Decimal = Decimal("1000.00"),
) -> Cuenta:
    cuenta = Cuenta(
        numero=f"CTA-{uuid4().hex[:10]}",
        tipo=TipoCuenta.ahorro,
        saldo=saldo,
        estado=EstadoCuenta.activa,
        usuario_id=usuario.id,
        organizacion_id=organizacion.id,
    )
    db.add(cuenta)
    db.flush()
    return cuenta


def _token(usuario: Usuario) -> str:
    return crear_token(
        {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "organizacion_id": str(usuario.organizacion_id),
        }
    )


def _headers(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(usuario)}"}


def _crear_dos_tenants(db: Session) -> tuple[Organizacion, Organizacion, Usuario, Usuario, Cuenta, Cuenta]:
    sufijo = uuid4().hex[:8]
    org_a = _crear_organizacion(db, f"aislamiento-a-{sufijo}")
    org_b = _crear_organizacion(db, f"aislamiento-b-{sufijo}")
    user_a = _crear_usuario(db, org_a, f"user-a-{sufijo}@example.com")
    user_b = _crear_usuario(db, org_b, f"user-b-{sufijo}@example.com")
    cuenta_a = _crear_cuenta(db, user_a, org_a)
    cuenta_b = _crear_cuenta(db, user_b, org_b)
    db.commit()
    return org_a, org_b, user_a, user_b, cuenta_a, cuenta_b


def test_usuario_org_a_no_ve_cuenta_org_b(client: TestClient, db_session: Session) -> None:
    _, _, user_a, _, cuenta_a, cuenta_b = _crear_dos_tenants(db_session)
    cuenta_a_id = cuenta_a.id
    cuenta_b_id = cuenta_b.id
    headers = _headers(user_a)

    r_lista = client.get("/cuentas/", headers=headers)
    assert r_lista.status_code == status.HTTP_200_OK, r_lista.text
    ids = {cuenta["id"] for cuenta in r_lista.json()}
    assert cuenta_a_id in ids
    assert cuenta_b_id not in ids

    r_detalle = client.get(f"/cuentas/{cuenta_b_id}", headers=headers)
    assert r_detalle.status_code == status.HTTP_404_NOT_FOUND


def test_usuario_org_a_no_transfiere_desde_cuenta_org_b(client: TestClient, db_session: Session) -> None:
    _, _, user_a, _, cuenta_a, cuenta_b = _crear_dos_tenants(db_session)
    cuenta_a_id = cuenta_a.id
    cuenta_b_id = cuenta_b.id
    headers = _headers(user_a)
    payload = {
        "cuenta_destino_id": cuenta_a_id,
        "monto": 10,
        "tipo": "transferencia",
        "descripcion": "origen cruzado",
    }

    r = client.post(
        f"/transacciones/?cuenta_origen_id={cuenta_b_id}",
        headers=headers,
        json=payload,
    )

    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_usuario_org_a_no_transfiere_hacia_cuenta_org_b(client: TestClient, db_session: Session) -> None:
    _, _, user_a, _, cuenta_a, cuenta_b = _crear_dos_tenants(db_session)
    cuenta_a_id = cuenta_a.id
    cuenta_b_id = cuenta_b.id
    headers = _headers(user_a)
    payload = {
        "cuenta_destino_id": cuenta_b_id,
        "monto": 10,
        "tipo": "transferencia",
        "descripcion": "destino cruzado",
    }

    r = client.post(
        f"/transacciones/?cuenta_origen_id={cuenta_a_id}",
        headers=headers,
        json=payload,
    )

    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert "organizaciones" in r.json()["detail"].lower()


def test_admin_org_a_no_congela_cuenta_org_b(client: TestClient, db_session: Session) -> None:
    org_a, _, _, _, _, cuenta_b = _crear_dos_tenants(db_session)
    admin_a = _crear_usuario(db_session, org_a, f"admin-a-{uuid4().hex[:8]}@example.com", RolUsuario.admin)
    db_session.commit()
    cuenta_b_id = cuenta_b.id
    headers = _headers(admin_a)

    r = client.put(
        f"/admin/cuentas/{cuenta_b_id}/estado",
        headers=headers,
        json={"nuevo_estado": "congelada"},
    )

    assert r.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
    cuenta_b_actual = db_session.get(Cuenta, cuenta_b_id)
    assert cuenta_b_actual is not None
    assert cuenta_b_actual.estado == EstadoCuenta.activa


def test_admin_org_a_no_lista_usuarios_org_b(client: TestClient, db_session: Session) -> None:
    org_a, _, _, user_b, _, _ = _crear_dos_tenants(db_session)
    admin_a = _crear_usuario(db_session, org_a, f"admin-list-{uuid4().hex[:8]}@example.com", RolUsuario.admin)
    db_session.commit()
    admin_a_email = admin_a.email
    user_b_email = user_b.email
    headers = _headers(admin_a)

    r = client.get("/admin/usuarios?limit=100", headers=headers)

    assert r.status_code == status.HTTP_200_OK, r.text
    emails = {usuario["email"] for usuario in r.json()}
    assert admin_a_email in emails
    assert user_b_email not in emails


def test_super_admin_puede_listar_organizaciones(client: TestClient, db_session: Session) -> None:
    org_a, org_b, _, _, _, _ = _crear_dos_tenants(db_session)
    super_admin = _crear_usuario(
        db_session,
        org_a,
        f"super-{uuid4().hex[:8]}@example.com",
        RolUsuario.SUPER_ADMIN,
    )
    db_session.commit()

    r = client.get("/organizaciones", headers=_headers(super_admin))

    assert r.status_code == status.HTTP_200_OK, r.text
    slugs = {org["slug"] for org in r.json()}
    assert org_a.slug in slugs
    assert org_b.slug in slugs


def test_organizacion_suspendida_no_puede_operar(client: TestClient, db_session: Session) -> None:
    slug = f"suspendida-{uuid4().hex[:8]}"
    org = _crear_organizacion(db_session, slug, EstadoOrganizacion.suspendida)
    usuario = _crear_usuario(db_session, org, f"user-{slug}@example.com")
    _crear_cuenta(db_session, usuario, org)
    db_session.commit()

    r = client.get("/cuentas/", headers=_headers(usuario))

    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert "organizacion" in r.json()["detail"].lower()
