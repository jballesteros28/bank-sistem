from __future__ import annotations

from fastapi.testclient import TestClient

from core.api import API_V1_PREFIX


def test_openapi_marca_endpoints_legacy_como_deprecated(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()

    for path, methods in openapi["paths"].items():
        if path.startswith("/cuentas") or path.startswith("/transacciones"):
            for method_data in methods.values():
                assert method_data["deprecated"] is True
                assert method_data["tags"][0].startswith("Legacy - ")


def test_openapi_presenta_wallet_saas(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()

    assert openapi["info"]["title"] == "Wallet SaaS API"
    assert openapi["info"]["version"] == "0.5.0"
    assert API_V1_PREFIX in openapi["info"]["description"]
    tag_names = {tag["name"] for tag in openapi["tags"]}
    assert {"Onboarding", "Wallets", "Movimientos", "Legacy - Cuentas", "Legacy - Transacciones"} <= tag_names


def test_endpoints_nuevos_documentan_respuesta_estandar(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()

    wallet_schema = openapi["paths"]["/wallets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    movimiento_schema = openapi["paths"]["/movimientos"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    organizacion_schema = openapi["paths"]["/organizaciones"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    for schema in (wallet_schema, movimiento_schema, organizacion_schema):
        ref = schema.get("$ref", "")
        assert "ApiResponse" in ref
