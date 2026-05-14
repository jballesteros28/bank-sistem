from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums.wallet_enum import MonedaWallet
from core.enums import EstadoCuenta, EstadoOrganizacion, RolUsuario, TipoCuenta
from core.seguridad import crear_token, hash_password
from models.cuenta import Cuenta
from models.organizacion import Organizacion
from models.usuario import Usuario


def _token(usuario: Usuario) -> str:
    payload = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return crear_token(payload)


def _headers(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(usuario)}"}


def _crear_organizacion(db: Session) -> Organizacion:
    sufijo = uuid4().hex[:10]
    organizacion = Organizacion(
        nombre=f"Org Mov {sufijo}",
        slug=f"org-mov-{sufijo}",
        email_contacto=f"mov-{sufijo}@example.com",
        estado=EstadoOrganizacion.activa,
    )
    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return organizacion


def _crear_usuario(db: Session, organizacion: Organizacion, rol: RolUsuario = RolUsuario.cliente) -> Usuario:
    sufijo = uuid4().hex[:10]
    usuario = Usuario(
        nombre=f"Usuario Mov {sufijo}",
        email=f"mov-{sufijo}@test.com",
        hashed_password=hash_password("pass1234"),
        es_activo=True,
        rol=rol,
        organizacion_id=organizacion.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _crear_wallet(
    db: Session,
    usuario: Usuario,
    *,
    saldo: Decimal = Decimal("0.00"),
    moneda: MonedaWallet = MonedaWallet.ARS,
    estado: EstadoCuenta = EstadoCuenta.activa,
) -> Cuenta:
    wallet = Cuenta(
        numero=f"CTA-{uuid4().hex[:8].upper()}",
        tipo=TipoCuenta.principal,
        alias=f"Mov {uuid4().hex[:6]}",
        moneda=moneda,
        saldo=saldo,
        estado=estado,
        usuario_id=usuario.id,
        organizacion_id=usuario.organizacion_id,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def _balance(client: TestClient, headers: dict[str, str], wallet_id: int) -> Decimal:
    response = client.get(f"/wallets/{wallet_id}/balance", headers=headers)
    assert response.status_code == 200, response.text
    return Decimal(response.json()["saldo"])


def test_deposito_admin_aumenta_saldo(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("10.00"))
    headers = _headers(admin)

    response = client.post(
        "/movimientos/deposito",
        headers=headers,
        json={"wallet_destino_id": wallet.id, "monto": "25.00", "descripcion": "Carga"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["tipo"] == "deposito"
    assert _balance(client, headers, wallet.id) == Decimal("35.00")


def test_cliente_no_puede_hacer_deposito_arbitrario(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente)

    response = client.post(
        "/movimientos/deposito",
        headers=_headers(cliente),
        json={"wallet_destino_id": wallet.id, "monto": "10.00"},
    )

    assert response.status_code == 403


def test_retiro_descuenta_saldo(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("100.00"))
    headers = _headers(cliente)

    response = client.post(
        "/movimientos/retiro",
        headers=headers,
        json={"wallet_origen_id": wallet.id, "monto": "30.00"},
    )

    assert response.status_code == 201, response.text
    assert _balance(client, headers, wallet.id) == Decimal("70.00")


def test_retiro_sin_saldo_suficiente_falla(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("5.00"))

    response = client.post(
        "/movimientos/retiro",
        headers=_headers(cliente),
        json={"wallet_origen_id": wallet.id, "monto": "10.00"},
    )

    assert response.status_code == 400
    assert "saldo" in response.json()["detail"].lower()


def test_transferencia_mueve_saldo_correctamente(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    emisor = _crear_usuario(db_session, org)
    receptor = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, emisor, saldo=Decimal("100.00"))
    destino = _crear_wallet(db_session, receptor, saldo=Decimal("20.00"))
    headers = _headers(emisor)
    receptor_headers = _headers(receptor)
    origen_id = origen.id
    destino_id = destino.id

    response = client.post(
        "/movimientos/transferencia",
        headers=headers,
        json={"wallet_origen_id": origen_id, "wallet_destino_id": destino_id, "monto": "40.00"},
    )

    assert response.status_code == 201, response.text
    assert _balance(client, headers, origen_id) == Decimal("60.00")
    assert _balance(client, receptor_headers, destino_id) == Decimal("60.00")


def test_pago_mueve_saldo_correctamente(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    cliente = _crear_usuario(db_session, org)
    comercio = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, cliente, saldo=Decimal("90.00"))
    destino = _crear_wallet(db_session, comercio, saldo=Decimal("10.00"))
    headers = _headers(cliente)

    response = client.post(
        "/movimientos/pago",
        headers=headers,
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "15.00"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["tipo"] == "pago"
    assert _balance(client, headers, origen.id) == Decimal("75.00")


def test_cashback_acredita_saldo(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("3.00"), moneda=MonedaWallet.PUNTOS)
    headers = _headers(admin)

    response = client.post(
        "/movimientos/cashback",
        headers=headers,
        json={"wallet_destino_id": wallet.id, "monto": "7.00"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["tipo"] == "cashback"
    assert _balance(client, headers, wallet.id) == Decimal("10.00")


def test_ajuste_admin_credito_aumenta_saldo(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("10.00"))
    headers = _headers(admin)

    response = client.post(
        "/movimientos/ajuste-admin",
        headers=headers,
        json={"wallet_destino_id": wallet.id, "monto": "5.00", "operacion": "credito", "motivo": "bonificacion"},
    )

    assert response.status_code == 201, response.text
    assert _balance(client, headers, wallet.id) == Decimal("15.00")


def test_ajuste_admin_debito_descuenta_saldo(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("10.00"))
    headers = _headers(admin)

    response = client.post(
        "/movimientos/ajuste-admin",
        headers=headers,
        json={"wallet_destino_id": wallet.id, "monto": "4.00", "operacion": "debito", "motivo": "correccion"},
    )

    assert response.status_code == 201, response.text
    assert _balance(client, headers, wallet.id) == Decimal("6.00")


def test_ajuste_admin_debito_sin_saldo_falla(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, saldo=Decimal("1.00"))

    response = client.post(
        "/movimientos/ajuste-admin",
        headers=_headers(admin),
        json={"wallet_destino_id": wallet.id, "monto": "4.00", "operacion": "debito", "motivo": "correccion"},
    )

    assert response.status_code == 400
    assert "saldo" in response.json()["detail"].lower()


def test_reversa_de_transferencia_vuelve_saldos(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    emisor = _crear_usuario(db_session, org)
    receptor = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, emisor, saldo=Decimal("100.00"))
    destino = _crear_wallet(db_session, receptor, saldo=Decimal("20.00"))
    emisor_headers = _headers(emisor)
    admin_headers = _headers(admin)

    transferencia = client.post(
        "/movimientos/transferencia",
        headers=emisor_headers,
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "30.00"},
    )
    assert transferencia.status_code == 201, transferencia.text
    movimiento_id = transferencia.json()["id"]

    reversa = client.post(
        f"/movimientos/{movimiento_id}/reversa",
        headers=admin_headers,
        json={"motivo_reversa": "error operativo"},
    )

    assert reversa.status_code == 201, reversa.text
    assert reversa.json()["tipo"] == "reversa"
    assert _balance(client, admin_headers, origen.id) == Decimal("100.00")
    assert _balance(client, admin_headers, destino.id) == Decimal("20.00")


def test_no_se_puede_revertir_dos_veces(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    emisor = _crear_usuario(db_session, org)
    receptor = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, emisor, saldo=Decimal("100.00"))
    destino = _crear_wallet(db_session, receptor)
    admin_headers = _headers(admin)

    transferencia = client.post(
        "/movimientos/transferencia",
        headers=_headers(emisor),
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "10.00"},
    )
    movimiento_id = transferencia.json()["id"]

    primera = client.post(
        f"/movimientos/{movimiento_id}/reversa",
        headers=admin_headers,
        json={"motivo_reversa": "primera"},
    )
    segunda = client.post(
        f"/movimientos/{movimiento_id}/reversa",
        headers=admin_headers,
        json={"motivo_reversa": "segunda"},
    )

    assert primera.status_code == 201, primera.text
    assert segunda.status_code == 400


def test_no_se_puede_operar_wallet_congelada(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    emisor = _crear_usuario(db_session, org)
    receptor = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, emisor, saldo=Decimal("50.00"), estado=EstadoCuenta.congelada)
    destino = _crear_wallet(db_session, receptor)

    response = client.post(
        "/movimientos/transferencia",
        headers=_headers(emisor),
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "5.00"},
    )

    assert response.status_code == 403
    assert "congelada" in response.json()["detail"].lower()


def test_no_se_puede_operar_wallet_cerrada(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    admin = _crear_usuario(db_session, org, RolUsuario.admin)
    cliente = _crear_usuario(db_session, org)
    wallet = _crear_wallet(db_session, cliente, estado=EstadoCuenta.cerrada)

    response = client.post(
        "/movimientos/deposito",
        headers=_headers(admin),
        json={"wallet_destino_id": wallet.id, "monto": "5.00"},
    )

    assert response.status_code == 403
    assert "cerrada" in response.json()["detail"].lower()


def test_no_se_puede_operar_entre_organizaciones(client: TestClient, db_session: Session) -> None:
    org_a = _crear_organizacion(db_session)
    org_b = _crear_organizacion(db_session)
    user_a = _crear_usuario(db_session, org_a)
    user_b = _crear_usuario(db_session, org_b)
    origen = _crear_wallet(db_session, user_a, saldo=Decimal("50.00"))
    destino = _crear_wallet(db_session, user_b)

    response = client.post(
        "/movimientos/transferencia",
        headers=_headers(user_a),
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "5.00"},
    )

    assert response.status_code == 403
    assert "organizaciones" in response.json()["detail"].lower()


def test_no_se_puede_operar_entre_monedas_distintas(client: TestClient, db_session: Session) -> None:
    org = _crear_organizacion(db_session)
    emisor = _crear_usuario(db_session, org)
    receptor = _crear_usuario(db_session, org)
    origen = _crear_wallet(db_session, emisor, saldo=Decimal("50.00"), moneda=MonedaWallet.ARS)
    destino = _crear_wallet(db_session, receptor, moneda=MonedaWallet.USD)

    response = client.post(
        "/movimientos/transferencia",
        headers=_headers(emisor),
        json={"wallet_origen_id": origen.id, "wallet_destino_id": destino.id, "monto": "5.00"},
    )

    assert response.status_code == 400
    assert "moneda" in response.json()["detail"].lower()


def test_get_movimientos_lista_solo_organizacion_actual(client: TestClient, db_session: Session) -> None:
    org_a = _crear_organizacion(db_session)
    org_b = _crear_organizacion(db_session)
    admin_a = _crear_usuario(db_session, org_a, RolUsuario.admin)
    admin_b = _crear_usuario(db_session, org_b, RolUsuario.admin)
    cliente_a = _crear_usuario(db_session, org_a)
    cliente_b = _crear_usuario(db_session, org_b)
    wallet_a = _crear_wallet(db_session, cliente_a)
    wallet_b = _crear_wallet(db_session, cliente_b)
    headers_a = _headers(admin_a)
    headers_b = _headers(admin_b)
    wallet_a_id = wallet_a.id
    wallet_b_id = wallet_b.id

    mov_a = client.post(
        "/movimientos/deposito",
        headers=headers_a,
        json={"wallet_destino_id": wallet_a_id, "monto": "1.00"},
    )
    mov_b = client.post(
        "/movimientos/deposito",
        headers=headers_b,
        json={"wallet_destino_id": wallet_b_id, "monto": "1.00"},
    )
    assert mov_a.status_code == 201, mov_a.text
    assert mov_b.status_code == 201, mov_b.text

    response = client.get("/movimientos", headers=headers_a)

    assert response.status_code == 200, response.text
    ids = {movimiento["id"] for movimiento in response.json()}
    assert mov_a.json()["id"] in ids
    assert mov_b.json()["id"] not in ids
