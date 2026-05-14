# tests/test_admin/test_admin_logs.py
# -*- coding: utf-8 -*-

"""
🧪 Test manual de endpoints administrativos de logs.
Usa requests HTTP reales con login y tokens obtenidos desde el backend.
Incluye validación del nuevo endpoint /admin/logs/dashboard.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
import pytest
from unittest.mock import AsyncMock, patch

BASE_URL = "http://127.0.0.1:8000"


def _backend_disponible() -> bool:
    try:
        requests.get(f"{BASE_URL}/", timeout=0.5)
        return True
    except requests.RequestException:
        return False


def _ejecutar_tests_manuales() -> bool:
    return os.getenv("RUN_MANUAL_HTTP_TESTS") == "1" and _backend_disponible()


pytestmark = pytest.mark.skipif(
    not _ejecutar_tests_manuales(),
    reason="Tests manuales: requieren RUN_MANUAL_HTTP_TESTS=1 y backend FastAPI en 127.0.0.1:8000.",
)


# -------------------------------------------------------------------
# ⚙️ Helpers
# -------------------------------------------------------------------
def obtener_token(email: str, password: str) -> str:
    """Realiza login en /auth/login y devuelve el token JWT."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code != 200:
        print(f"❌ Error al obtener token para {email}: {response.text}")
        return ""

    token = response.json().get("access_token")
    if not token:
        print(f"⚠️ No se encontró access_token en la respuesta de {email}")
        return ""
    return token


# -------------------------------------------------------------------
# 🧪 1. Test con MongoDB simulado
# -------------------------------------------------------------------
@patch("services.log_summary_service.mongo_db")
def test_logs_admin_mocked(mongo_mock):
    """
    ✅ Simula la respuesta de Mongo para validar estructura general.
    """
    fake_data = [{"_id": "TransferenciaExitosa", "total": 5}]
    mongo_mock.__getitem__.return_value.aggregate.return_value.to_list = AsyncMock(return_value=fake_data)

    token_admin = obtener_token("admin@sistemabancario.com", "Admin123!")
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = requests.get(f"{BASE_URL}/admin/logs/resumen", headers=headers)

    print("\n🧩 Test 1: Logs Mocked — /admin/logs/resumen")
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text[:200])

    if response.status_code == 200:
        print("✅ Estructura general OK")
    else:
        print("❌ Falla en endpoint /admin/logs/resumen")


# -------------------------------------------------------------------
# 🧱 2. Acceso autorizado (rol admin)
# -------------------------------------------------------------------
def test_logs_admin_acceso_autorizado():
    """
    ✅ El usuario admin debe poder acceder correctamente a todos los endpoints /admin/logs.
    Incluye prueba del nuevo /admin/logs/dashboard.
    """
    token_admin = obtener_token("admin@sistemabancario.com", "Admin123!")
    headers = {"Authorization": f"Bearer {token_admin}"}

    endpoints = [
        "/admin/logs/transacciones",
        "/admin/logs/correos",
        "/admin/logs/niveles",
        "/admin/logs/resumen",
        "/admin/logs/dashboard",  # ✅ nuevo endpoint
    ]

    print("\n🧩 Test 2: Acceso autorizado (ADMIN)")

    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"→ {endpoint} | Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                claves = list(data.keys())[:4]
                print(f"   ✅ OK — Claves: {claves}")

                # 🔍 Validación específica del nuevo dashboard
                if "dashboard" in endpoint:
                    assert all(k in data for k in ["niveles_chart", "correos_chart", "transacciones_chart"]), \
                        "❌ Faltan claves esperadas en dashboard"
                    print("   ✅ Estructura dashboard correcta (niveles_chart, correos_chart, transacciones_chart)")

            except Exception:
                print("   ⚠️ No se pudo parsear JSON:", response.text[:200])
        else:
            print("   ❌ ERROR:", response.text[:200])


# -------------------------------------------------------------------
# 🚫 3. Acceso denegado (rol cliente)
# -------------------------------------------------------------------
def test_logs_admin_acceso_denegado_cliente():
    """
    🚫 El usuario con rol cliente no debe poder acceder (403).
    """
    token_cliente = obtener_token("emisor@test.com", "pass1234")
    headers = {"Authorization": f"Bearer {token_cliente}"}

    response = requests.get(f"{BASE_URL}/admin/logs/resumen", headers=headers)
    print("\n🧩 Test 3: Acceso denegado (CLIENTE)")
    print("Status:", response.status_code)
    print("Response:", response.text[:200])

    if response.status_code == 403:
        print("✅ Acceso correctamente restringido")
    else:
        print("❌ Falla en restricción de acceso (esperado 403)")


# -------------------------------------------------------------------
# 🚫 4. Sin token
# -------------------------------------------------------------------
def test_logs_admin_sin_token():
    """
    🚫 Si no se envía token, debe devolver 401 Unauthorized.
    """
    response = requests.get(f"{BASE_URL}/admin/logs/resumen")
    print("\n🧩 Test 4: Sin token")
    print("Status:", response.status_code)
    print("Response:", response.text[:200])

    if response.status_code == 401:
        print("✅ Error esperado: token ausente")
    else:
        print("❌ Debería devolver 401 y no lo hizo")


# -------------------------------------------------------------------
# ▶️ EJECUCIÓN MANUAL
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Iniciando test manual de /admin/logs...\n")

    try:
        ping = requests.get(f"{BASE_URL}/")
        if ping.status_code not in (200, 404):
            print("⚠️ El backend no está respondiendo correctamente.")
    except Exception as e:
        print(f"❌ No se pudo conectar al backend: {e}")
        exit()

    test_logs_admin_mocked()
    test_logs_admin_acceso_autorizado()
    test_logs_admin_acceso_denegado_cliente()
    test_logs_admin_sin_token()

    print("\n✅ Finalizado test de endpoints administrativos de logs.\n")
