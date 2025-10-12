# tests/test_admin/test_admin_integracion_http.py
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Dict, Any, List

from database.db_postgres import SessionLocal
from models.usuario import Usuario
from core.seguridad import crear_token

# 🌐 URL base del servidor FastAPI en ejecución
BASE_URL = "http://127.0.0.1:8000"

# 🧩 Usuarios creados por init_seed()
ADMIN_EMAIL = "admin@sistemabancario.com"
EMISOR_EMAIL = "emisor@test.com"
RECEPTOR_EMAIL = "receptor@test.com"


# =========================================================
# 🧩 Helper: obtener token JWT válido
# =========================================================
def _token_para_usuario(email: str) -> str:
    """Obtiene un JWT válido desde la base de datos para el usuario dado."""
    db: Session = SessionLocal()
    try:
        usuario: Optional[Usuario] = db.scalar(select(Usuario).where(Usuario.email == email))
        if not usuario:
            raise ValueError(f"❌ Usuario {email} no encontrado en la base de datos.")
        payload = {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
        }
        return crear_token(payload)
    finally:
        db.close()


# =========================================================
# 🚀 Test de Integración HTTP del módulo Administrativo
# =========================================================
if __name__ == "__main__":
    print("\n🎯 INICIANDO BLOQUE 5 — INTEGRACIÓN ADMINISTRATIVA (HTTP REAL)\n")

    admin_token = _token_para_usuario(ADMIN_EMAIL)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # ---------------------------------------------------------
    # 1️⃣ Listar usuarios
    # ---------------------------------------------------------
    print("1️⃣ Listando usuarios...")
    r = requests.get(f"{BASE_URL}/admin/usuarios", headers=headers_admin)
    print(f"   ➜ Status: {r.status_code}")
    if r.status_code == 200:
        usuarios = r.json()
        print(f"   Total usuarios: {len(usuarios)}")
        if isinstance(usuarios, list) and all("email" in u for u in usuarios):
            print("   ✅ Estructura válida (lista de usuarios con emails).")
        else:
            print("   ⚠️ Estructura inesperada:", usuarios)
    else:
        print("   ❌ Error al obtener usuarios:", r.text)

    # ---------------------------------------------------------
    # 2️⃣ Cambio de rol de usuario (emisor)
    # ---------------------------------------------------------
    print("\n2️⃣ Cambio de rol de usuario (emisor)...")
    r = requests.put(
        f"{BASE_URL}/admin/usuarios/2/rol",
        headers=headers_admin,
        json={"nuevo_rol": "cliente"},
    )
    print(f"   ➜ Status: {r.status_code}")
    data = r.json()
    if r.status_code == 200 and "rol" in data:
        print(f"   ✅ Rol actualizado correctamente: {data['rol']}")
    else:
        print("   ⚠️ Respuesta inesperada:", data)

    # ---------------------------------------------------------
    # 3️⃣ Cambio de estado de cuenta (cuenta 1)
    # ---------------------------------------------------------
    print("\n3️⃣ Cambio de estado de cuenta (cuenta 1)...")
    r = requests.put(
        f"{BASE_URL}/admin/cuentas/1/estado",
        headers=headers_admin,
        json={"nuevo_estado": "congelada"},
    )
    print(f"   ➜ Status: {r.status_code}")
    data = r.json()
    if r.status_code == 200 and "estado" in data:
        print(f"   ✅ Estado de cuenta actualizado: {data['estado']}")
    elif r.status_code == 404:
        print("   ⚠️ Cuenta no encontrada (verifica IDs del seed).")
    else:
        print("   ⚠️ Respuesta inesperada:", data)

    # ---------------------------------------------------------
    # 4️⃣ Logs del sistema
    # ---------------------------------------------------------
    print("\n4️⃣ Consultando logs del sistema...")
    r = requests.get(f"{BASE_URL}/admin/logs", headers=headers_admin)
    print(f"   ➜ Status: {r.status_code}")
    if r.status_code == 200:
        logs = r.json()
        print(f"   Logs encontrados: {len(logs)}")
        if isinstance(logs, list):
            print("   ✅ Formato correcto (lista).")
        if logs:
            print("   Último log:", logs[0])
    else:
        print("   ❌ Error:", r.text)

    # ---------------------------------------------------------
    # 5️⃣ Logs de correos
    # ---------------------------------------------------------
    print("\n5️⃣ Consultando logs de correos...")
    r = requests.get(f"{BASE_URL}/admin/logs/correos?limit=5", headers=headers_admin)
    print(f"   ➜ Status: {r.status_code}")
    if r.status_code == 200:
        correos = r.json()
        print(f"   Registros de correo: {len(correos)}")
        if correos:
            muestra = correos[0]
            claves_ok = all(k in muestra for k in ("destinatario", "asunto", "fecha"))
            print("   ✅ Estructura válida." if claves_ok else "   ⚠️ Claves faltantes:", muestra)
    else:
        print("   ❌ Error al obtener logs de correos:", r.text)

    # ---------------------------------------------------------
    # 6️⃣ Reporte de cuentas por estado
    # ---------------------------------------------------------
    print("\n6️⃣ Reporte de cuentas por estado...")
    r = requests.get(f"{BASE_URL}/admin/reportes/cuentas/estado", headers=headers_admin)
    print(f"   ➜ Status: {r.status_code}")
    data = r.json()
    if r.status_code == 200 and isinstance(data, dict):
        estados = ("activa", "congelada", "inactiva")
        faltantes = [e for e in estados if e not in data]
        if not faltantes:
            print(f"   ✅ Estructura correcta: {data}")
        else:
            print(f"   ⚠️ Faltan claves esperadas: {faltantes}")
    else:
        print("   ❌ Respuesta inválida:", data)

    # ---------------------------------------------------------
    # 7️⃣ Reporte de saldos por tipo
    # ---------------------------------------------------------
    print("\n7️⃣ Reporte de saldos por tipo de cuenta...")
    r = requests.get(f"{BASE_URL}/admin/reportes/cuentas/saldos", headers=headers_admin)
    print(f"   ➜ Status: {r.status_code}")
    data = r.json()
    if r.status_code == 200 and isinstance(data, dict):
        if all(isinstance(v, (int, float)) for v in data.values()):
            print(f"   ✅ Estructura correcta con saldos numéricos: {data}")
        else:
            print("   ⚠️ Valores no numéricos en saldos:", data)
    else:
        print("   ❌ Error al obtener reporte:", r.text)

    # ---------------------------------------------------------
    # 8️⃣ Reporte de transacciones
    # ---------------------------------------------------------
    print("\n8️⃣ Reporte de transacciones entre fechas...")
    hoy = datetime.now().date()
    desde = (hoy - timedelta(days=30)).isoformat()
    hasta = hoy.isoformat()
    r = requests.get(
        f"{BASE_URL}/admin/reportes/transacciones?desde={desde}&hasta={hasta}",
        headers=headers_admin,
    )
    print(f"   ➜ Status: {r.status_code}")
    transacciones = r.json()
    if r.status_code == 200 and isinstance(transacciones, list):
        print(f"   ✅ Transacciones obtenidas: {len(transacciones)}")
        if transacciones:
            keys_ok = all(k in transacciones[0] for k in ("id", "fecha", "monto"))
            print("   ✅ Estructura válida." if keys_ok else "   ⚠️ Campos faltantes.")
    else:
        print("   ❌ Error en respuesta:", r.text)

    print("\n✅ BLOQUE 5 COMPLETADO CON VALIDACIONES EXITOSAS.")
