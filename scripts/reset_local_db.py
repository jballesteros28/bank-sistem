"""Reset de base local para desarrollo: downgrade, upgrade y seed demo."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings


def _masked_database_url() -> str:
    try:
        return make_url(settings.DATABASE_URL).render_as_string(hide_password=True)
    except Exception:
        return "<DATABASE_URL invalida>"


def _database_safety_issues() -> list[str]:
    issues: list[str] = []
    try:
        url = make_url(settings.DATABASE_URL)
    except Exception as exc:
        return [f"No se pudo parsear DATABASE_URL: {exc}"]

    database_name = (url.database or "").lower()
    host = (url.host or "").lower()
    if "wallet_saas" not in database_name:
        issues.append("El nombre de base en DATABASE_URL debe contener 'wallet_saas'.")
    if host not in {"localhost", "127.0.0.1", "postgres"}:
        issues.append("DATABASE_URL debe apuntar a localhost, 127.0.0.1 o al servicio Docker postgres.")
    return issues


def _ensure_dev_database_safety(*, allow_unsafe_database: bool = False) -> None:
    if settings.ENVIRONMENT.strip().lower() == "production":
        raise SystemExit("Abortado: reset_local_db.py no puede correr con ENVIRONMENT=production.")

    issues = _database_safety_issues()
    if not issues:
        return

    print("")
    print("ADVERTENCIA FUERTE: la base configurada no parece ser la base local de desarrollo.")
    print(f"ENVIRONMENT={settings.ENVIRONMENT}")
    print(f"DATABASE_URL={_masked_database_url()}")
    for issue in issues:
        print(f"- {issue}")
    if not allow_unsafe_database:
        raise SystemExit(
            "Abortado por seguridad. Si realmente es una base local de desarrollo, "
            "reintenta con --allow-unsafe-database."
        )
    print("Continuando porque se paso --allow-unsafe-database.")


def _confirm_reset(*, yes: bool) -> None:
    if yes:
        return
    print("", flush=True)
    print("Esta accion borra y recrea el esquema de la base local configurada.", flush=True)
    print(f"ENVIRONMENT={settings.ENVIRONMENT}", flush=True)
    print(f"DATABASE_URL={_masked_database_url()}", flush=True)
    confirmation = input("Escribi RESET para continuar: ").strip()
    if confirmation != "RESET":
        raise SystemExit("Reset cancelado.")


def _run_step(name: str, command: list[str]) -> None:
    print("", flush=True)
    print(f"==> {name}", flush=True)
    print(subprocess.list2cmdline(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT_DIR, stderr=subprocess.STDOUT)
    if completed.returncode != 0:
        raise SystemExit(f"Fallo el paso '{name}' con codigo {completed.returncode}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resetea la base local y carga datos demo.")
    parser.add_argument("--yes", action="store_true", help="Confirma el reset sin pedir input interactivo.")
    parser.add_argument(
        "--allow-unsafe-database",
        action="store_true",
        help="Permite correr si DATABASE_URL no parece wallet_saas local. Nunca saltea ENVIRONMENT=production.",
    )
    args = parser.parse_args()

    _ensure_dev_database_safety(allow_unsafe_database=args.allow_unsafe_database)
    _confirm_reset(yes=args.yes)

    seed_command = [sys.executable, str(ROOT_DIR / "scripts" / "dev_seed.py")]
    if args.allow_unsafe_database:
        seed_command.append("--allow-unsafe-database")

    _run_step("Alembic downgrade base", [sys.executable, "-m", "alembic", "downgrade", "base"])
    _run_step("Alembic upgrade head", [sys.executable, "-m", "alembic", "upgrade", "head"])
    _run_step("Seed demo", seed_command)

    print("")
    print("Reset local listo.")
    print("- Super admin: superadmin@demo.com / Password123!")
    print("- Owner: owner@demo.com / Password123!")
    print("- Admin: admin@demo.com / Password123!")
    print("- Soporte: soporte@demo.com / Password123!")
    print("- Cliente: cliente@demo.com / Password123!")


if __name__ == "__main__":
    main()
