# Wallet SaaS API

Backend modular para una plataforma Wallet SaaS multi-tenant. El dominio publico gira alrededor de organizaciones, usuarios, wallets, movimientos, onboarding, admin, auditoria y notificaciones.

## Stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- MongoDB para logs externos o integraciones futuras
- JWT con `python-jose`
- Pydantic v2
- Alembic
- pytest

## Estructura

```text
app/
  main.py
  core/
  shared/
  apps/
    auth/
    usuarios/
    organizaciones/
    onboarding/
    wallets/
    movimientos/
    admin/
    auditoria/
    notificaciones/
    planes/
  middlewares/
alembic/
tests/
```

## Instalacion

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Crear un `.env` desde `.env.example` y ajustar `DATABASE_URL`, `MONGO_URI`, `SECRET_KEY` y variables SMTP si se usan notificaciones por correo.

## Validacion local con PostgreSQL

1. Crear la base local `wallet_saas` en PostgreSQL.
2. Configurar `DATABASE_URL` en `.env` con usuario, password, host, puerto y base correctos.
3. Ejecutar `python -m alembic upgrade head`.
4. Ejecutar `python -m alembic current` y confirmar la revision `head`.
5. Levantar el backend con `uvicorn app.main:app --reload`.
6. Abrir `http://127.0.0.1:8000/docs` y validar `http://127.0.0.1:8000/health`.

Los tests usan una base aislada de test configurada en `tests/conftest.py`; no deben ejecutarse contra la base local principal.

Si `psycopg2` muestra un mensaje con encoding ilegible, verificar primero que PostgreSQL este activo y que usuario, password, base, host y puerto de `DATABASE_URL` sean correctos. No ocultar el error silenciosamente: corregir la configuracion y repetir la migracion.

## Comandos

```bash
alembic upgrade head
uvicorn app.main:app --reload
pytest -q
```

## Endpoints principales

- `GET /health`
- `POST /api/v1/onboarding/registro-organizacion`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/organizaciones`
- `GET /api/v1/usuarios`
- `GET /api/v1/wallets`
- `POST /api/v1/movimientos/deposito`
- `POST /api/v1/movimientos/transferencia`
- `POST /api/v1/movimientos/retiro`
- `POST /api/v1/movimientos/{movimiento_id}/reversa`
- `GET /api/v1/admin/resumen`
- `GET /api/v1/auditoria`
- `GET /api/v1/notificaciones`
- `GET /api/v1/planes`
- `GET /api/v1/planes/organizacion/actual`
- `PATCH /api/v1/planes/organizaciones/{organizacion_id}/cambiar-plan`
- `GET /api/v1/organizaciones/me/branding`
- `PATCH /api/v1/organizaciones/me/branding`

## Planes SaaS

Cada organizacion puede tener un plan comercial asociado. El onboarding asigna `Free` por defecto y los limites se aplican por organizacion al crear usuarios, wallets y movimientos aprobados del mes actual.

Planes base:

- `free`: 10 usuarios, 3 wallets, 100 movimientos mensuales.
- `starter`: 100 usuarios, 50 wallets, 2000 movimientos mensuales.
- `pro`: 1000 usuarios, wallets ilimitadas, 50000 movimientos mensuales, webhooks y white label.
- `enterprise`: usuarios, wallets y movimientos ilimitados, webhooks y white label.

Cuando un limite es `NULL`, se interpreta como ilimitado.

Endpoints principales:

- `POST /api/v1/planes`: crea planes, solo `super_admin`.
- `GET /api/v1/planes`: lista planes.
- `GET /api/v1/planes/{plan_id}`: obtiene un plan.
- `PATCH /api/v1/planes/{plan_id}`: edita planes, solo `super_admin`.
- `GET /api/v1/planes/organizacion/actual`: consulta el plan actual para `owner`, `admin` o `super_admin`.
- `PATCH /api/v1/planes/organizaciones/{organizacion_id}/cambiar-plan`: cambia el plan de una organizacion, solo `super_admin`.

## Branding por organizacion

Cada organizacion puede configurar su marca visual y preferencias operativas:

- `nombre_comercial`
- `logo_url`
- `color_primario` y `color_secundario` en formato HEX
- `subdominio`
- `dominio_personalizado`
- `moneda_default`
- `timezone`
- `permite_white_label_activo`

El onboarding inicializa `nombre_comercial` con el nombre de la organizacion, `moneda_default` en `ARS` y `timezone` en `America/Argentina/Buenos_Aires`.

El `subdominio` es unico y puede configurarse en cualquier plan. El `dominio_personalizado` y la activacion de white-label requieren un plan compatible, es decir, un plan con `permite_white_label=True` como `pro` o `enterprise`.

Endpoints principales:

- `GET /api/v1/organizaciones/me/branding`: obtiene el branding de la organizacion actual.
- `PATCH /api/v1/organizaciones/me/branding`: actualiza el branding de la organizacion actual para `owner` o `admin`.
- `GET /api/v1/organizaciones/{organizacion_id}/branding`: consulta branding respetando permisos de organizacion.
- `PATCH /api/v1/organizaciones/{organizacion_id}/branding`: actualiza branding; `super_admin` puede operar cualquier organizacion.
