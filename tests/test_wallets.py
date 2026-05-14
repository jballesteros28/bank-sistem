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


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _organizacion_demo(db: Session) -> Organizacion:
    organizacion = db.query(Organizacion).filter_by(slug="organizacion-demo").first()
    assert organizacion is not None
    return organizacion


def _crear_organizacion(db: Session) -> Organizacion:
    sufijo = uuid4().hex[:10]
    organizacion = Organizacion(
        nombre=f"Org Wallet {sufijo}",
        slug=f"org-wallet-{sufijo}",
        email_contacto=f"org-{sufijo}@example.com",
        estado=EstadoOrganizacion.activa,
    )
    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return organizacion


def _crear_usuario(db: Session, organizacion: Organizacion, rol: RolUsuario = RolUsuario.cliente) -> Usuario:
    sufijo = uuid4().hex[:10]
    usuario = Usuario(
        nombre=f"Usuario Wallet {sufijo}",
        email=f"wallet-{sufijo}@test.com",
        hashed_password=hash_password("pass1234"),
        es_activo=True,
        rol=rol,
        organizacion_id=organizacion.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _crear_wallet_db(
    db: Session,
    usuario: Usuario,
    *,
    saldo: Decimal = Decimal("0.00"),
    moneda: MonedaWallet = MonedaWallet.ARS,
    limite_operacion: Decimal | None = None,
    estado: EstadoCuenta = EstadoCuenta.activa,
) -> Cuenta:
    cuenta = Cuenta(
        numero=f"CTA-{uuid4().hex[:8].upper()}",
        tipo=TipoCuenta.principal,
        alias=f"Wallet {uuid4().hex[:6]}",
        moneda=moneda,
        saldo=saldo,
        limite_operacion=limite_operacion,
        es_principal=False,
        estado=estado,
        usuario_id=usuario.id,
        organizacion_id=usuario.organizacion_id,
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta


def test_crear_wallet(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    organizacion_id = str(usuario.organizacion_id)

    response = client.post(
        "/wallets",
        headers=_headers(usuario),
        json={"alias": "Principal", "tipo": "principal", "moneda": "ARS", "es_principal": True},
    )

    assert response.status_code == 201, response.text
    data = _data(response)
    assert data["alias"] == "Principal"
    assert data["tipo"] == "principal"
    assert data["estado"] == "activa"
    assert data["saldo"] == "0.00"
    assert data["organizacion_id"] == organizacion_id


def test_listar_wallets_del_usuario(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    _crear_wallet_db(db_session, usuario)
    _crear_wallet_db(db_session, usuario, moneda=MonedaWallet.USD)

    response = client.get("/wallets", headers=_headers(usuario))

    assert response.status_code == 200, response.text
    data = _data(response)
    assert len(data) == 2
    assert {wallet["usuario_id"] for wallet in data} == {usuario.id}


def test_no_ver_wallet_de_otra_organizacion(client: TestClient, db_session: Session) -> None:
    usuario_demo = _crear_usuario(db_session, _organizacion_demo(db_session))
    usuario_otro = _crear_usuario(db_session, _crear_organizacion(db_session))
    wallet_ajena = _crear_wallet_db(db_session, usuario_otro)

    response = client.get(f"/wallets/{wallet_ajena.id}", headers=_headers(usuario_demo))

    assert response.status_code == 404


def test_obtener_balance_wallet(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    wallet = _crear_wallet_db(db_session, usuario, saldo=Decimal("42.50"))

    response = client.get(f"/wallets/{wallet.id}/balance", headers=_headers(usuario))

    assert response.status_code == 200, response.text
    assert _data(response)["saldo"] == "42.50"


def test_cambiar_estado_wallet(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    wallet = _crear_wallet_db(db_session, usuario)

    response = client.patch(
        f"/wallets/{wallet.id}/estado",
        headers=_headers(usuario),
        json={"estado": "congelada"},
    )

    assert response.status_code == 200, response.text
    assert _data(response)["estado"] == "congelada"


def test_congelar_wallet_bloquea_operacion(client: TestClient, db_session: Session) -> None:
    organizacion = _organizacion_demo(db_session)
    emisor = _crear_usuario(db_session, organizacion)
    receptor = _crear_usuario(db_session, organizacion)
    origen = _crear_wallet_db(db_session, emisor, saldo=Decimal("200.00"))
    destino = _crear_wallet_db(db_session, receptor)
    headers = _headers(emisor)
    origen_id = origen.id
    destino_id = destino.id

    client.patch(
        f"/wallets/{origen_id}/estado",
        headers=headers,
        json={"estado": "congelada"},
    )
    response = client.post(
        f"/transacciones/?wallet_origen_id={origen_id}",
        headers=headers,
        json={"wallet_destino_id": destino_id, "monto": 10, "tipo": "transferencia"},
    )

    assert response.status_code == 403
    assert "origen" in response.json()["detail"].lower()


def test_cerrar_wallet_con_saldo_cero(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    wallet = _crear_wallet_db(db_session, usuario, saldo=Decimal("0.00"))

    response = client.patch(f"/wallets/{wallet.id}/cerrar", headers=_headers(usuario))

    assert response.status_code == 200, response.text
    assert _data(response)["estado"] == "cerrada"


def test_no_cerrar_wallet_con_saldo_mayor_a_cero(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))
    wallet = _crear_wallet_db(db_session, usuario, saldo=Decimal("10.00"))

    response = client.patch(f"/wallets/{wallet.id}/cerrar", headers=_headers(usuario))

    assert response.status_code == 400
    assert "saldo" in response.json()["detail"].lower()


def test_crear_wallet_en_moneda_puntos(client: TestClient, db_session: Session) -> None:
    usuario = _crear_usuario(db_session, _organizacion_demo(db_session))

    response = client.post(
        "/wallets",
        headers=_headers(usuario),
        json={"alias": "Puntos", "tipo": "recompensas", "moneda": "PUNTOS"},
    )

    assert response.status_code == 201, response.text
    assert _data(response)["moneda"] == "PUNTOS"


def test_bloquear_transferencia_entre_wallets_de_distinta_moneda(
    client: TestClient,
    db_session: Session,
) -> None:
    organizacion = _organizacion_demo(db_session)
    emisor = _crear_usuario(db_session, organizacion)
    receptor = _crear_usuario(db_session, organizacion)
    origen = _crear_wallet_db(db_session, emisor, saldo=Decimal("200.00"), moneda=MonedaWallet.ARS)
    destino = _crear_wallet_db(db_session, receptor, moneda=MonedaWallet.USD)

    response = client.post(
        f"/transacciones/?wallet_origen_id={origen.id}",
        headers=_headers(emisor),
        json={"wallet_destino_id": destino.id, "monto": 10, "tipo": "transferencia"},
    )

    assert response.status_code == 400
    assert "moneda" in response.json()["detail"].lower()


def test_respetar_limite_operacion(client: TestClient, db_session: Session) -> None:
    organizacion = _organizacion_demo(db_session)
    emisor = _crear_usuario(db_session, organizacion)
    receptor = _crear_usuario(db_session, organizacion)
    origen = _crear_wallet_db(
        db_session,
        emisor,
        saldo=Decimal("200.00"),
        limite_operacion=Decimal("50.00"),
    )
    destino = _crear_wallet_db(db_session, receptor)

    response = client.post(
        f"/transacciones/?wallet_origen_id={origen.id}",
        headers=_headers(emisor),
        json={"wallet_destino_id": destino.id, "monto": 100, "tipo": "transferencia"},
    )

    assert response.status_code == 400
    assert "limite" in response.json()["detail"].lower()
