from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.integraciones.models import APIKey, WebhookEndpoint
from app.apps.movimientos.models import Movimiento
from app.apps.organizaciones.models import Organizacion
from app.apps.recompensas.models import AplicacionRecompensa, ReglaRecompensa
from app.apps.usuarios.models import Usuario
from app.apps.wallets.models import Wallet
from scripts.dev_seed import (
    DEMO_API_KEY_NAME,
    DEMO_ORG,
    DEMO_REWARD_REFERENCE,
    DEMO_REWARD_RULE_NAME,
    DEMO_USERS,
    DEMO_WEBHOOK_NAME,
    seed_demo,
)


def test_seed_demo_crea_roles_wallets_movimientos_y_no_duplica(db_session: Session) -> None:
    first = seed_demo(db_session)
    second = seed_demo(db_session)

    assert first["organizacion_id"] == second["organizacion_id"]
    assert first["wallet_empresa_id"] == second["wallet_empresa_id"]
    assert first["wallet_cliente_id"] == second["wallet_cliente_id"]
    assert first["api_key_demo_id"] == second["api_key_demo_id"]
    assert first["webhook_demo_id"] == second["webhook_demo_id"]
    assert first["regla_recompensa_id"] == second["regla_recompensa_id"]
    assert first["aplicacion_recompensa_id"] == second["aplicacion_recompensa_id"]
    assert first["api_key_raw"]
    assert second["api_key_raw"] == ""

    org = db_session.scalar(select(Organizacion).where(Organizacion.slug == DEMO_ORG["slug"]))
    assert org is not None

    demo_emails = [str(user_data["email"]) for user_data in DEMO_USERS.values()]
    users = db_session.scalars(select(Usuario).where(Usuario.email.in_(demo_emails))).all()
    assert len(users) == len(demo_emails)
    assert {user.email: user.rol.value for user in users} == {
        str(user_data["email"]): user_data["rol"].value for user_data in DEMO_USERS.values()
    }

    wallets = db_session.scalars(
        select(Wallet).where(
            Wallet.organizacion_id == org.id,
            Wallet.alias.in_(
                [
                    "Wallet Empresa Demo",
                    "Wallet Cliente Demo",
                    "Wallet Owner Demo",
                    "Wallet Admin Demo",
                ]
            ),
        )
    ).all()
    assert len(wallets) == 4
    assert {wallet.alias: wallet.saldo for wallet in wallets} == {
        "Wallet Empresa Demo": Decimal("50000.00"),
        "Wallet Cliente Demo": Decimal("10000.00"),
        "Wallet Owner Demo": Decimal("5000.00"),
        "Wallet Admin Demo": Decimal("3000.00"),
    }

    references = [
        "seed-deposito-cliente",
        "seed-pago-cliente-organizacion",
        "seed-cashback-cliente",
        DEMO_REWARD_REFERENCE,
        "seed-ajuste-organizacion",
    ]
    movements = db_session.scalars(select(Movimiento).where(Movimiento.referencia_externa.in_(references))).all()
    assert len(movements) == 5
    assert {movement.referencia_externa for movement in movements} == set(references)

    regla = db_session.scalar(select(ReglaRecompensa).where(ReglaRecompensa.nombre == DEMO_REWARD_RULE_NAME))
    aplicacion = db_session.scalar(
        select(AplicacionRecompensa).where(AplicacionRecompensa.referencia_externa == DEMO_REWARD_REFERENCE)
    )
    assert regla is not None
    assert regla.porcentaje_cashback == Decimal("10.00")
    assert regla.monto_minimo_compra == Decimal("1000.00")
    assert regla.monto_maximo_recompensa == Decimal("2000.00")
    assert aplicacion is not None
    assert aplicacion.regla_id == regla.id
    assert aplicacion.monto_compra == Decimal("15000.00")
    assert aplicacion.monto_recompensa == Decimal("1500.00")

    api_keys = db_session.scalars(select(APIKey).where(APIKey.nombre == DEMO_API_KEY_NAME)).all()
    assert len(api_keys) == 1
    assert api_keys[0].activa is False
    assert api_keys[0].scopes == ["wallets:read", "movimientos:read", "movimientos:write"]

    webhooks = db_session.scalars(select(WebhookEndpoint).where(WebhookEndpoint.nombre == DEMO_WEBHOOK_NAME)).all()
    assert len(webhooks) == 1
    assert webhooks[0].activo is False
    assert webhooks[0].url == "https://example.com/webhook-demo"
    assert "recompensa.aplicada" in webhooks[0].eventos
