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

## IDs publicos

Los IDs publicos principales usan UUID: organizaciones, planes, usuarios, wallets, movimientos, auditoria y notificaciones. En desarrollo se puede resetear la DB local cuando cambie la migracion inicial.

Reset local recomendado:

```bash
dropdb wallet_saas
createdb wallet_saas
python -m alembic upgrade head
```

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
- `POST /api/v1/wallets/organizacion`
- `GET /api/v1/wallets/organizacion`
- `GET /api/v1/wallets/organizacion/principal`
- `POST /api/v1/movimientos/deposito`
- `POST /api/v1/movimientos/transferencia`
- `POST /api/v1/movimientos/retiro`
- `POST /api/v1/movimientos/pago`
- `POST /api/v1/movimientos/pago-organizacion`
- `POST /api/v1/movimientos/{movimiento_id}/reversa`
- `GET /api/v1/admin/resumen`
- `GET /api/v1/auditoria`
- `GET /api/v1/notificaciones`
- `GET /api/v1/notificaciones/no-leidas/count`
- `PATCH /api/v1/notificaciones/{notificacion_id}/leida`
- `PATCH /api/v1/notificaciones/marcar-todas-leidas`
- `GET /api/v1/planes`
- `GET /api/v1/planes/organizacion/actual`
- `PATCH /api/v1/planes/organizaciones/{organizacion_id}/cambiar-plan`
- `GET /api/v1/organizaciones/me/branding`
- `PATCH /api/v1/organizaciones/me/branding`

## Wallets

El SaaS maneja wallets internas por organizacion. No es banco, no custodia dinero real inicialmente y no reintroduce lenguaje financiero legacy. Las wallets representan saldos internos, puntos, cashback, caja operativa y pagos dentro de cada organizacion.

Cada wallet tiene `owner_type`:

- `usuario`: la wallet pertenece a un usuario. Usa `usuario_id` y deja `organizacion_owner_id=NULL`.
- `organizacion`: la wallet pertenece a la organizacion. Usa `organizacion_owner_id` y deja `usuario_id=NULL`.

`organizacion_id` siempre existe y define el aislamiento multi-tenant. El backend lo resuelve desde el usuario autenticado, o desde la organizacion gestionada cuando opera un `super_admin`; el frontend no es fuente confiable para ese dato.

Tipos principales:

- Wallets de usuario: `principal`, `ahorro`, `recompensas`.
- Wallets de organizacion: `empresa`, `operativa`, `caja`, `recompensas`.

Casos soportados:

- Pagos internos desde usuarios hacia la organizacion.
- Caja y saldo operativo de la organizacion.
- Programas de recompensas, puntos o cashback.
- Separacion entre saldo de usuarios y saldo propio del comercio, empresa, comunidad o plataforma.

El onboarding crea dos wallets en la misma operacion atomica: la wallet principal del owner y la wallet principal de la organizacion (`Wallet empresa`). La creacion de cualquier wallet consume `limite_wallets` del plan.

Endpoints principales:

- `POST /api/v1/wallets`: crea wallets de usuario.
- `GET /api/v1/wallets`: lista wallets de usuario visibles segun permisos.
- `POST /api/v1/wallets/organizacion`: crea wallets de organizacion para `owner`, `admin` o `super_admin`.
- `GET /api/v1/wallets/organizacion`: lista wallets de organizacion para `owner`, `admin`, `soporte` o `super_admin`.
- `GET /api/v1/wallets/organizacion/principal`: obtiene la wallet principal de la organizacion.

## Movimientos

Los movimientos registran cambios de saldo internos dentro de una organizacion. Todo movimiento aprobado consume `limite_movimientos_mes`. El modelo distingue operaciones de una sola wallet de operaciones entre dos wallets:

- Operaciones con una wallet:
  - `deposito`: acredita una wallet destino. `wallet_origen_id=NULL`.
  - `retiro`: debita una wallet origen. `wallet_destino_id=NULL`.
  - `cashback`: acredita una wallet destino. `wallet_origen_id=NULL`.
  - `ajuste_admin`: puede ser `credito` o `debito`; el credito usa solo destino y el debito usa solo origen.
- Operaciones entre dos wallets:
  - `transferencia`: debita origen y acredita destino.
  - `pago`: debita origen y acredita destino.
  - `pago-organizacion`: debita una wallet de usuario y acredita una wallet de organizacion.

`wallet_origen_id` y `wallet_destino_id` son opcionales en la tabla `movimientos` para representar correctamente depositos, retiros, cashback, ajustes y reversas. Las operaciones entre dos wallets requieren ambos IDs y bloquean origen y destino iguales.

Las reversas son contables: no borran el movimiento original. El backend crea un movimiento tipo `reversa`, guarda `movimiento_origen_id`, marca el original como `revertida` y mueve el saldo inverso segun el tipo original:

- Deposito, cashback o ajuste credito: debita la wallet destino original.
- Retiro o ajuste debito: acredita la wallet origen original.
- Transferencia, pago o pago a organizacion: debita el destino original y acredita el origen original.

Flujo comercial usuario a organizacion:

1. El usuario paga desde una wallet `owner_type=usuario`.
2. La wallet destino debe ser `owner_type=organizacion`.
3. Ambas wallets deben estar activas, pertenecer a la misma organizacion y usar la misma moneda.
4. El backend debita la wallet del usuario, acredita la wallet de la organizacion, crea el movimiento tipo `pago`, registra auditoria y genera notificaciones.

Endpoint especifico:

- `POST /api/v1/movimientos/pago-organizacion`: pago comercial interno desde usuario hacia organizacion.

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

## Notificaciones y emails

El backend genera notificaciones internas para eventos reales del SaaS: onboarding exitoso, wallets creadas o congeladas, movimientos y suspension de organizaciones. Los clientes ven sus propias notificaciones; `owner` y `admin` ven las de su organizacion; `super_admin` puede consultar globalmente.

Los emails de evento se crean como notificaciones de canal `email` y se agendan con `BackgroundTasks` despues de completar la operacion principal. Un error de email no debe romper la creacion de la organizacion, wallet o movimiento.

Configurar `EMAILS_ENABLED=true` junto con `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_STARTTLS` y `MAIL_SSL_TLS` para habilitar envios reales. Con `EMAILS_ENABLED=false`, o en ambiente `test`, el modo silencioso evita envios reales.

Endpoints principales:

- `GET /api/v1/notificaciones`: lista notificaciones internas segun permisos.
- `GET /api/v1/notificaciones/no-leidas/count`: muestra la cantidad de notificaciones no leidas.
- `PATCH /api/v1/notificaciones/{notificacion_id}/leida`: marca una notificacion como leida.
- `PATCH /api/v1/notificaciones/marcar-todas-leidas`: marca todas las notificaciones visibles como leidas.
- `GET /api/v1/notificaciones/organizacion`: vista administrativa por organizacion.
