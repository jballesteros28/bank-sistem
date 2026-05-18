# Wallet SaaS API

Backend modular para una plataforma Wallet SaaS multi-tenant. El dominio publico gira alrededor de organizaciones, usuarios, wallets internas, movimientos, recompensas, onboarding, admin, auditoria y notificaciones.

## Stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- MongoDB para logs externos o integraciones futuras
- JWT con `python-jose`
- Pydantic v2
- Alembic
- pytest
- React + Vite para el frontend

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
    recompensas/
    ecommerce/
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

Los IDs publicos principales usan UUID: organizaciones, planes, usuarios, wallets, movimientos, recompensas, ecommerce, auditoria y notificaciones.

## Entorno local de pruebas

Estos comandos son solo para desarrollo local. Los scripts abortan con `ENVIRONMENT=production` y tambien frenan si `DATABASE_URL` no apunta a una base local cuyo nombre contenga `wallet_saas`, salvo que se use el flag explicito `--allow-unsafe-database`.

Reset completo de base local, migraciones y datos demo:

```bash
python scripts/reset_local_db.py --yes
```

Solo cargar o actualizar el seed demo:

```bash
python scripts/dev_seed.py
```

Levantar backend:

```bash
uvicorn app.main:app --reload
```

Levantar frontend:

```bash
npm run dev
```

Accesos demo:

- Super admin: `superadmin@demo.com` / `Password123!`
- Owner: `owner@demo.com` / `Password123!`
- Admin: `admin@demo.com` / `Password123!`
- Soporte: `soporte@demo.com` / `Password123!`
- Cliente: `cliente@demo.com` / `Password123!`

El seed deja lista la organizacion `Demo Wallet` en plan `Starter`, usuarios para todos los roles, wallet empresa con saldo, wallets de owner/admin/cliente, movimientos demo, regla y aplicacion de recompensa demo, notificaciones demo, una API Key demo ecommerce activa y un webhook demo inactivo. Es idempotente para desarrollo: reutiliza los registros demo existentes, restablece saldos/credenciales y no duplica datos base.

Datos demo principales:

- Organizacion: `Demo Wallet` (`demo-wallet`)
- Plan demo: `Starter`, para permitir auto-creacion de clientes y wallets durante pruebas ecommerce.
- Wallet empresa: `Wallet Empresa Demo`, saldo `50000 ARS`
- Wallet cliente: `Wallet Cliente Demo`, saldo `10000 ARS`
- Wallet owner: `Wallet Owner Demo`, saldo `5000 ARS`
- Wallet admin: `Wallet Admin Demo`, saldo `3000 ARS`
- Movimientos seed: `seed-deposito-cliente`, `seed-pago-cliente-organizacion`, `seed-cashback-cliente`, `seed-recompensa-demo`, `seed-ajuste-organizacion`
- Regla recompensa: `Cashback Demo 10%`, compra minima `1000 ARS`, tope `2000 ARS`, recompensa demo esperada `1500 ARS`
- API Key demo: activa por defecto, scopes `wallets:read`, `movimientos:read`, `movimientos:write`, `ecommerce:read`, `ecommerce:write`
- Webhook demo: inactivo, URL `https://example.com/webhook-demo`, eventos `movimiento.creado`, `pago_organizacion.creado`, `ecommerce.order_paid`, `ecommerce.order_processed`, `ecommerce.order_failed` y `recompensa.aplicada`

Que probar manualmente:

- Login owner.
- Dashboard owner.
- Usuarios.
- Wallets.
- Movimientos.
- Integraciones.
- Recompensas.
- Ecommerce en `/ecommerce`.
- Developer Portal en `/developer` con owner, admin, soporte o super admin.
- Login cliente.
- Dashboard cliente.
- Pago a organizacion.
- Mis recompensas en `/recompensas`.
- Confirmar que cliente no ve Developer en el sidebar.
- Confirmar que cliente no ve Ecommerce en el sidebar.

## Comandos

```bash
alembic upgrade head
python scripts/dev_seed.py
uvicorn app.main:app --reload
pytest -q
```

Frontend:

```bash
npm install
npm run dev
npm run lint
npm run build
npm run preview
```

## Docker local

El entorno Docker local levanta PostgreSQL, backend y frontend con Compose. No usa secretos reales y corre con `ENVIRONMENT=development`; para produccion real hay que reemplazar secrets, DB y dominios.

Construir y levantar:

```bash
docker compose build
docker compose up
```

Cuando el backend este listo, cargar datos demo opcionales:

```bash
docker compose exec backend python scripts/dev_seed.py
```

URLs:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`

Accesos demo despues del seed:

- Owner: `owner@demo.com` / `Password123!`
- Cliente: `cliente@demo.com` / `Password123!`

Reset del entorno Docker:

```bash
docker compose down -v
docker compose up --build
docker compose exec backend python scripts/dev_seed.py
```

Troubleshooting:

- Puertos ocupados: ajustar `3000:80`, `8000:8000` o `5432:5432` en `docker-compose.yml`.
- Docker Desktop en Windows: si `docker version` muestra `Access is denied` contra `.docker/config.json` o `//./pipe/docker_engine`, iniciar Docker Desktop, usar el contexto `desktop-linux` y correr la terminal con permisos para acceder al daemon.
- Cambios de `VITE_API_BASE_URL`: reconstruir el frontend porque Vite hornea variables en build.
- CORS: Compose local permite `http://localhost:3000` y `http://127.0.0.1:3000`.
- Migraciones: el backend ejecuta `python -m alembic upgrade head` al iniciar.
- Postgres health: `backend` espera `pg_isready`; si `/ready` falla, revisar logs de `postgres` y `backend`.
- PowerShell + curl: si un JSON inline devuelve `422 json_invalid`, guardar el payload en un archivo y usar `curl.exe --data-binary "@payload.json"`.

## Preparacion para produccion

La guia completa esta en [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). El orden recomendado para deploy real es: primero backend en Railway con PostgreSQL, despues frontend en Vercel apuntando a la URL publica del backend.

Backend Railway:

- Variables obligatorias: `ENVIRONMENT=production`, `DEBUG=false`, `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `FRONTEND_URL`, `BACKEND_URL` y `LOG_LEVEL=INFO`.
- `DATABASE_URL` debe apuntar al PostgreSQL administrado de Railway. Usar el formato SQLAlchemy `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB_NAME`.
- `SECRET_KEY` debe ser largo y aleatorio; `change-me` y valores cortos son rechazados en production.
- `CORS_ORIGINS` se configura como CSV real, por ejemplo `https://wallet-demo.vercel.app`; no usar `*` en production.
- Railway usa `Dockerfile.backend`, `railway.json` y `sh scripts/docker_start.sh`; ese script ejecuta `python -m alembic upgrade head` antes de levantar Uvicorn.
- Health checks disponibles: `GET /health` y `GET /ready`; Railway usa `/ready` para validar DB.
- `EMAILS_ENABLED=true` solo cuando SMTP este configurado.

Frontend Vercel:

- Variables Vite: `VITE_API_BASE_URL=https://<backend-railway>.up.railway.app`, `VITE_API_PREFIX=/api/v1` y `VITE_APP_NAME=Wallet SaaS`.
- Build command: `npm run build`; output directory: `dist`.
- `vercel.json` reescribe `/(.*)` a `/index.html` para que `/dashboard`, `/wallets`, `/ecommerce` y otras rutas SPA funcionen al refrescar.
- Los ejemplos curl del Developer Portal usan localhost como sandbox local; para produccion reemplazar host y API Key por datos del entorno real.

Checklist:

- Cambiar `SECRET_KEY`.
- Crear PostgreSQL en Railway y configurar `DATABASE_URL`.
- Deployar backend en Railway y verificar `/ready`.
- Deployar frontend en Vercel con `VITE_API_BASE_URL` apuntando al backend Railway.
- Configurar `CORS_ORIGINS` y `FRONTEND_URL` con el dominio final de Vercel y redeployar backend si Railway no reinicia automaticamente.
- No ejecutar `scripts/reset_local_db.py` ni `scripts/dev_seed.py` en produccion.
- No versionar `.env`, `.env.local`, secretos, API Keys ni webhook secrets.

Validacion frontend completada en FASE 14.1.1:

- `npm install`: OK, con `package-lock.json` generado.
- `npm run lint`: OK.
- `npm run build`: OK.
- `npm run dev`: OK en `http://127.0.0.1:5173`.
- Rutas validadas: `/login`, `/onboarding`, `/dashboard`, `/wallets`, `/movimientos`.
- Las rutas privadas renderizan login cuando no hay token.

## Endpoints principales

- `GET /health`
- `POST /api/v1/onboarding/registro-organizacion`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/organizaciones`
- `GET /api/v1/usuarios`
- `POST /api/v1/usuarios`
- `GET /api/v1/usuarios/{usuario_id}`
- `PATCH /api/v1/usuarios/{usuario_id}`
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
- `POST /api/v1/recompensas/reglas`
- `GET /api/v1/recompensas/reglas`
- `POST /api/v1/recompensas/simular`
- `POST /api/v1/recompensas/aplicar`
- `GET /api/v1/recompensas/aplicaciones`
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
- `POST /api/v1/integraciones/api-keys`
- `GET /api/v1/integraciones/webhooks`
- `POST /api/v1/integraciones/webhooks/deliveries/{delivery_id}/reenviar`
- `GET /api/v1/ext/wallets/{wallet_id}`
- `POST /api/v1/ext/movimientos/deposito`
- `POST /api/v1/ext/movimientos/cashback`
- `POST /api/v1/ext/ecommerce/order-paid`
- `GET /api/v1/ecommerce/orders`
- `GET /api/v1/ecommerce/orders/{event_id}`

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
  - `credito_tienda`: acredita credito interno o puntos en una wallet destino. `wallet_origen_id=NULL`.
  - `ajuste_admin`: puede ser `credito` o `debito`; el credito usa solo destino y el debito usa solo origen.
- Operaciones entre dos wallets:
  - `transferencia`: debita origen y acredita destino.
  - `pago`: debita origen y acredita destino.
  - `pago-organizacion`: debita una wallet de usuario y acredita una wallet de organizacion.

`wallet_origen_id` y `wallet_destino_id` son opcionales en la tabla `movimientos` para representar correctamente depositos, retiros, cashback, credito de tienda, ajustes y reversas. Las operaciones entre dos wallets requieren ambos IDs y bloquean origen y destino iguales.

Las reversas son contables: no borran el movimiento original. El backend crea un movimiento tipo `reversa`, guarda `movimiento_origen_id`, marca el original como `revertida` y mueve el saldo inverso segun el tipo original:

- Deposito, cashback, credito de tienda o ajuste credito: debita la wallet destino original.
- Retiro o ajuste debito: acredita la wallet origen original.
- Transferencia, pago o pago a organizacion: debita el destino original y acredita el origen original.

Flujo comercial usuario a organizacion:

1. El usuario paga desde una wallet `owner_type=usuario`.
2. La wallet destino debe ser `owner_type=organizacion`.
3. Ambas wallets deben estar activas, pertenecer a la misma organizacion y usar la misma moneda.
4. El backend debita la wallet del usuario, acredita la wallet de la organizacion, crea el movimiento tipo `pago`, registra auditoria y genera notificaciones.

Endpoint especifico:

- `POST /api/v1/movimientos/pago-organizacion`: pago comercial interno desde usuario hacia organizacion.

## Recompensas / Store Credit

El modulo de recompensas permite que cada organizacion configure reglas de fidelizacion para acreditar cashback, puntos o credito interno en wallets del usuario. No representa dinero real ni saldos bancarios: es valor virtual usable dentro de la organizacion.

Una regla de recompensa define nombre, tipo, estado, moneda de recompensa, porcentaje de cashback o monto fijo, compra minima, tope maximo, vigencia y si es acumulable. El backend siempre resuelve `organizacion_id` desde el usuario autenticado o el alcance del `super_admin`; el frontend no es fuente confiable para asignar una regla a otra organizacion.

Tipos soportados:

- `cashback`: calcula un porcentaje sobre la compra y acredita un movimiento tipo `cashback`.
- `puntos`: acredita puntos en una wallet `PUNTOS` usando movimiento `credito_tienda`.
- `credito_tienda`: acredita saldo interno en `ARS`, `USD` o `PUNTOS` usando movimiento `credito_tienda`.

Calculo:

- Si la regla tiene `porcentaje_cashback`, recompensa = `monto_compra * porcentaje / 100`.
- Si la regla tiene `monto_fijo`, acredita ese monto.
- Si existe `monto_maximo_recompensa`, se aplica como tope.
- Si la compra no alcanza `monto_minimo_compra`, la regla no aplica.
- Las reglas `inactiva`, `pausada` o fuera de vigencia no aplican.

Ejemplo: una tienda registra una compra externa de `$20.000` y tiene una regla de cashback del `10%`; el cliente recibe `$2.000` virtuales en su wallet interna de la organizacion.

Aplicar una recompensa valida usuario, wallet, organizacion y moneda; acredita la wallet destino, crea movimiento, guarda auditoria en `aplicaciones_recompensa`, genera notificacion interna y dispara el webhook `recompensa.aplicada` cuando hay endpoints activos. Si se informa `referencia_externa`, no se permite duplicar la misma referencia dentro de la organizacion.

Endpoints principales:

- `POST /api/v1/recompensas/reglas`: crea una regla para `owner`, `admin` o `super_admin`.
- `GET /api/v1/recompensas/reglas`: lista reglas visibles para `owner`, `admin`, `soporte` o `super_admin`.
- `GET /api/v1/recompensas/reglas/{regla_id}`: obtiene una regla.
- `PATCH /api/v1/recompensas/reglas/{regla_id}`: edita o cambia estado de una regla.
- `POST /api/v1/recompensas/simular`: calcula si una compra recibiria recompensa sin acreditar saldo.
- `POST /api/v1/recompensas/aplicar`: aplica la recompensa y crea movimiento.
- `GET /api/v1/recompensas/aplicaciones`: lista aplicaciones de la organizacion.
- `GET /api/v1/recompensas/aplicaciones/me`: lista recompensas del usuario autenticado.

## Ecommerce Integration

Wallet SaaS no procesa dinero real. El pago real ocurre fuera del sistema, por ejemplo en Tienda Nube, Shopify, WooCommerce, Mercado Pago u otra tienda. Cuando la tienda confirma una compra pagada, llama a `POST /api/v1/ext/ecommerce/order-paid` con una API Key de la organizacion y el backend acredita una recompensa interna si hay una regla activa aplicable.

La auditoria visual del flujo esta disponible en `/ecommerce` para `owner`, `admin`, `soporte` y `super_admin`.

Flujo:

1. El ecommerce envia proveedor, `external_order_id`, email del cliente, monto y moneda.
2. El backend toma `organizacion_id` desde la API Key, nunca desde el payload publico.
3. Se deduplica por `organizacion_id + proveedor + external_order_id`.
4. Si el cliente no existe en esa organizacion, se crea automaticamente con rol `cliente`, password temporal no expuesta y wallet interna.
5. Si hay regla de recompensa activa, se crea `aplicaciones_recompensa`, movimiento interno, notificacion y auditoria con `actor_tipo=api_key`.

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid \
  -H "X-API-Key: wsk_test_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "proveedor": "generic",
    "external_order_id": "order-1001",
    "customer_email": "cliente@demo.com",
    "customer_name": "Cliente Demo",
    "amount": 20000,
    "currency": "ARS",
    "metadata": {
      "source": "tienda-nube-demo"
    }
  }'
```

Scopes:

- `ecommerce:write` para `POST /api/v1/ext/ecommerce/order-paid`.
- `ecommerce:read` queda disponible para integraciones que necesiten lectura futura; los endpoints internos de consulta usan JWT.

Eventos webhook salientes:

- `ecommerce.order_paid`
- `ecommerce.order_processed`
- `ecommerce.order_failed`
- `recompensa.aplicada` cuando se acredita recompensa.

Si no hay regla aplicable, el evento queda procesado con `error_procesamiento="No hay regla de recompensa aplicable"` y se dispara `ecommerce.order_failed`. Si la orden se repite, el endpoint devuelve `409` con `La orden ya fue procesada.`. La moneda del payload debe estar soportada por wallets internas (`ARS`, `USD` o `PUNTOS`).

## Integraciones

Las organizaciones pueden conectar sistemas externos mediante API Keys y Webhooks. Las API Keys pertenecen siempre a una organizacion, no reemplazan el login JWT y no se guardan en texto plano. La key real se muestra solo al crearla; luego el backend conserva `key_prefix` para identificacion y `key_hash` para validacion.

La auditoria distingue el actor que origina cada evento:

- `usuario`: acciones autenticadas con JWT. Se guarda `actor_usuario_id`.
- `api_key`: acciones en `/api/v1/ext` autenticadas con API Key. Se guarda `actor_api_key_id` y no se simula un usuario.
- `sistema`: acciones internas o de background, como envios de webhooks o emails.

Scopes iniciales:

- `wallets:read`
- `wallets:write`
- `movimientos:read`
- `movimientos:write`
- `ecommerce:read`
- `ecommerce:write`
- `usuarios:read`
- `usuarios:write`
- `webhooks:read`
- `webhooks:write`

Uso externo:

```http
X-API-Key: wsk_test_xxxxxxxxx
```

Endpoints externos iniciales:

- `GET /api/v1/ext/wallets/{wallet_id}` requiere `wallets:read`.
- `POST /api/v1/ext/movimientos/deposito` requiere `movimientos:write`.
- `POST /api/v1/ext/movimientos/cashback` requiere `movimientos:write`.
- `POST /api/v1/ext/ecommerce/order-paid` requiere `ecommerce:write`.
- `GET /api/v1/ext/movimientos` requiere `movimientos:read`.

Los endpoints externos operan solo dentro de la organizacion de la API Key. Nunca aceptan `organizacion_id` como fuente confiable.

Webhooks:

- Los endpoints se administran en `POST/GET/PATCH/DELETE /api/v1/integraciones/webhooks`.
- Cada webhook define `url`, `eventos` y un `secret` usado para firmar.
- El `secret` se guarda cifrado con Fernet derivado desde `SECRET_KEY`; nunca se devuelve en listados ni responses de administracion.
- Cada delivery incluye firma HMAC SHA256 en `X-Wallet-Signature`.
- Tambien se envian `X-Wallet-Event` y `X-Wallet-Delivery-Id`.
- Los errores de envio no bloquean la operacion principal; quedan registrados como deliveries `fallido`.
- El envio en background abre una sesion DB propia y no reutiliza la sesion del request original.
- `POST /api/v1/integraciones/webhooks/deliveries/{delivery_id}/reenviar` permite a `owner`, `admin` y `super_admin` reintentar deliveries `fallido` o `pendiente`. `soporte` no puede reenviar, y un tenant no puede reenviar deliveries de otra organizacion.

Eventos soportados:

- `wallet.creada`
- `movimiento.creado`
- `movimiento.revertido`
- `pago_organizacion.creado`
- `ecommerce.order_paid`
- `ecommerce.order_processed`
- `ecommerce.order_failed`
- `recompensa.aplicada`
- `notificacion.creada`
- `organizacion.suspendida`

Planes:

- `free` y `starter` no permiten crear webhooks porque `permite_webhooks=False`.
- `pro` y `enterprise` habilitan webhooks.
- Las API Keys pueden usarse en todos los planes, pero los endpoints siguen respetando limites de wallets y movimientos del plan.

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

## Frontend React

El frontend esta creado con React + Vite en JavaScript, sin TypeScript. La decision permite avanzar rapido sobre una base modular manteniendo claridad con JSDoc en `src/shared/docs/apiShapes.js`, validaciones Zod y separacion por features.

Stack frontend:

- React
- Vite
- JavaScript (`.js` y `.jsx`)
- React Router
- Axios
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Tailwind CSS

Variables requeridas en `.env` o `.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api/v1
VITE_APP_NAME=Wallet SaaS
```

No versionar `.env` real. `.env.example` ya incluye las variables del backend y frontend.

Estructura frontend:

```text
src/
  app/              # router, providers y QueryClient
  shared/           # API client, UI, layouts, hooks, utils y shapes JSDoc
  features/         # auth, onboarding, dashboard, wallets, movimientos, etc.
  styles/           # Tailwind global y variables de tema
```

Rutas:

- Publicas: `/login`, `/onboarding`
- Privadas: `/dashboard`, `/wallets`, `/movimientos`, `/notificaciones`, `/branding`, `/planes`, `/integraciones`, `/recompensas`, `/developer`, `/usuarios`

Flujo Auth + Onboarding validado para FASE 14.2:

1. Ir a `/onboarding`.
2. Crear la organizacion con `nombre`, `slug` y `email_contacto`.
3. Crear el owner con `nombre`, `email`, `password` y confirmacion de password.
4. El frontend envia `POST /api/v1/onboarding/registro-organizacion` con:

```json
{
  "organizacion": {
    "nombre": "Mi Comercio",
    "slug": "mi-comercio",
    "email_contacto": "contacto@micomercio.test"
  },
  "owner": {
    "nombre": "Owner Demo",
    "email": "owner@micomercio.test",
    "password": "Password123!"
  }
}
```

5. Al crear correctamente, redirige a `/login` con un mensaje de exito.
6. Login usa `POST /api/v1/auth/login` con JSON `{ "email": "...", "password": "..." }`. El backend devuelve `access_token` y `token_type`.
7. El frontend guarda el token, consulta `GET /api/v1/auth/me`, guarda el usuario y redirige a `/dashboard`.
8. Al recargar una ruta privada, Zustand hidrata desde `localStorage`; si hay token sin usuario, `ProtectedRoute` vuelve a consultar `/auth/me`.
9. Si `/auth/me` devuelve `401`, se limpia la sesion y se redirige a `/login`.
10. `GET /api/v1/organizaciones/me/branding` se consulta post-login para mostrar `nombre_comercial`, `logo_url` y aplicar `color_primario`/`color_secundario`.

Credenciales de prueba:

- Para el entorno local seed/demo: `superadmin@demo.com`, `owner@demo.com`, `admin@demo.com`, `soporte@demo.com` y `cliente@demo.com` usan `Password123!`.
- Tambien se puede crear una organizacion nueva desde `/onboarding` y usar el email/password del owner creado.

El cliente HTTP usa `VITE_API_BASE_URL + VITE_API_PREFIX`, agrega `Authorization: Bearer <token>`, desempaqueta respuestas `{ success, message, data }` y limpia la sesion ante `401`. El token queda en `localStorage` por ahora; queda marcado el TODO para migrar a cookies HttpOnly en produccion.

El branding dinamico se prepara desde `GET /api/v1/organizaciones/me/branding` y aplica `nombre_comercial`, `logo_url`, `color_primario` y `color_secundario` al layout cuando hay sesion.

### Validacion E2E Auth + Onboarding

Levantar backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Validar backend:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/docs
curl http://127.0.0.1:8000/openapi.json
```

Levantar frontend:

```bash
npm run dev -- --host 127.0.0.1 --port 5174
```

Variables frontend esperadas, por `.env`, `.env.local` o defaults del cliente HTTP:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api/v1
```

Flujo probado contra backend real:

- `/onboarding`: crear organizacion con slug unico, owner y password `Password123!`.
- Redireccion a `/login` con mensaje de exito.
- `/login`: autenticar owner creado.
- Guardado de token y usuario en `localStorage`.
- `/dashboard`: muestra usuario, rol `owner`, organizacion/branding y cards iniciales.
- Refresh de `/dashboard`: mantiene sesion y revalida `/auth/me`.
- Logout: elimina token/user y vuelve a `/login`.
- `/wallets` sin token: redirige a `/login`.
- Token invalido en `localStorage`: `/auth/me` responde `401`, se limpia sesion y redirige a `/login`.

Datos de ejemplo usados en E2E:

```text
Organizacion: Demo Wallet E2E UI
Slug: demo-wallet-ui-YYYYMMDDHHMMSS
Email contacto: demo-ui-YYYYMMDDHHMMSS@example.com
Owner: Owner Demo
Owner email: owner-ui-YYYYMMDDHHMMSS@example.com
Password: Password123!
```

Troubleshooting:

- Si el navegador muestra `Network Error` pero `curl`/PowerShell contra la API funciona, revisar `CORS_ORIGINS` en `.env`.
- Si una ruta privada vuelve a `/login`, revisar que exista `wallet_saas_token` y que `GET /api/v1/auth/me` devuelva `200`.
- Si el token esta vencido o malformado, el comportamiento esperado es `401`, limpieza de storage y redireccion a `/login`.
- Si Vite cambia de puerto, agregar ese origin a `CORS_ORIGINS` o iniciar Vite explicitamente con `--port 5173`.

Validacion local completada:

- `GET /health`, `/docs` y `/openapi.json`: OK.
- UI E2E con Chrome headless/CDP: OK.
- `npm run lint`: OK.
- `npm run build`: OK.
- `python -m pytest -q`: OK.

### Dashboard Owner

El dashboard privado de `/dashboard` muestra informacion real para usuarios `owner`, `admin` y roles de consulta autenticados. Tambien degrada por seccion si un endpoint no aplica al rol actual, por ejemplo `soporte` o `super_admin` sin organizacion asociada.

Endpoints consumidos:

- `GET /api/v1/planes/organizacion/actual`
- `GET /api/v1/wallets/organizacion`
- `GET /api/v1/wallets/organizacion/principal`
- `GET /api/v1/movimientos?skip=0&limit=5`
- `GET /api/v1/notificaciones/no-leidas/count`
- `GET /api/v1/organizaciones/me/branding`

Datos visibles:

- Saludo con nombre y rol del usuario.
- Nombre comercial de la organizacion desde branding.
- Plan actual, precio mensual, limites de usuarios, wallets y movimientos.
- Flags de webhooks y white-label.
- Total de wallets de organizacion.
- Wallet principal de organizacion con alias, tipo, moneda, estado y saldo.
- Ultimos movimientos visibles para la organizacion.
- Cantidad de notificaciones no leidas.
- Accesos rapidos a wallets, movimientos, branding e integraciones.

Limitaciones actuales:

- Los accesos rapidos navegan a las secciones existentes; todavia no abren modales ni crean recursos directamente desde el dashboard.
- Los movimientos recientes muestran los ultimos 5 registros disponibles sin filtros avanzados.
- Si un endpoint falla por permisos o falta de organizacion, el dashboard conserva las demas secciones y muestra el error puntual.

Validacion FASE 14.3:

- UI E2E owner: onboarding, login, dashboard real, refresh, logout y token invalido OK.
- Dashboard owner mostro `Free`, limite de 3 wallets, `Wallet empresa`, saldo ARS, movimientos recientes y notificaciones no leidas.
- Endpoints del dashboard respondieron `200` durante la prueba UI.

### Dashboard Cliente

El rol `cliente` ahora tiene una experiencia propia en `/dashboard`, separada del panel operativo de la organizacion. La pantalla se enfoca en saldo, pagos, movimientos personales y notificaciones, sin mostrar planes, integraciones, branding ni usuarios.

Endpoints consumidos:

- `GET /api/v1/wallets`: obtiene solo las wallets de usuario visibles para el cliente.
- `GET /api/v1/movimientos?skip=0&limit=5`: obtiene los movimientos recientes asociados a sus wallets.
- `GET /api/v1/notificaciones/no-leidas/count`: muestra pendientes personales.
- `GET /api/v1/organizaciones/me/branding`: muestra el nombre comercial de la organizacion.
- `POST /api/v1/movimientos/pago-organizacion`: registra pagos desde una wallet de usuario hacia una wallet de organizacion.

Datos visibles:

- Saludo personalizado y nombre comercial de la organizacion.
- Wallet principal del cliente, o la primera wallet disponible si ninguna viene marcada como principal.
- Alias, saldo, moneda, estado y tipo de wallet.
- Ultimos movimientos con tipo, monto, moneda, estado y fecha.
- Contador de notificaciones no leidas.
- Accesos a pagar a organizacion, movimientos y notificaciones.

Pago a organizacion:

- El formulario permite seleccionar una wallet origen activa del cliente.
- El destino se ingresa manualmente como `wallet_destino_id`, porque el cliente no puede listar wallets de organizacion con el contrato actual.
- Si no hay wallet activa, la accion queda bloqueada con empty state.
- Si no hay saldo suficiente, el backend responde `Saldo insuficiente.` y la UI muestra el error.
- Al pagar correctamente, se invalidan queries de `movimientos`, `wallets` y `dashboard`.

Flujo cliente:

1. Un owner/admin crea un usuario `cliente` desde `/usuarios`.
2. Un owner/admin crea o asigna una wallet de usuario para ese cliente si hace falta.
3. El cliente inicia sesion y entra a `/dashboard`.
4. Puede consultar sus wallets en `/wallets`, sus movimientos en `/movimientos` y sus notificaciones en `/notificaciones`.
5. Puede pagar a una wallet de organizacion si conoce el ID destino y tiene saldo suficiente.

Limitaciones actuales:

- Crear un cliente desde `/usuarios` no crea automaticamente una wallet principal. Queda pendiente para una fase backend futura: auto-crear wallet principal para nuevos usuarios `cliente`.
- El cliente no puede descubrir wallets de organizacion desde UI; necesita que la organizacion le comparta el ID de destino.
- El dashboard cliente carga hasta 5 movimientos recientes; los filtros completos siguen en `/movimientos`.

### Wallets UI

La ruta privada `/wallets` deja de ser placeholder y muestra una pantalla funcional para consultar wallets de organizacion y wallets de usuario. La vista usa TanStack Query por seccion para que un error puntual no bloquee toda la pagina, y React Hook Form + Zod para crear wallets de organizacion.

Endpoints consumidos:

- `GET /api/v1/wallets`: lista wallets de usuario visibles segun permisos.
- `GET /api/v1/wallets/organizacion`: lista wallets de organizacion.
- `GET /api/v1/wallets/organizacion/principal`: obtiene la wallet principal activa de la organizacion.
- `POST /api/v1/wallets/organizacion`: crea una wallet de organizacion.

Payload de creacion de wallet de organizacion:

```json
{
  "alias": "Caja sucursal centro",
  "tipo": "caja",
  "moneda": "ARS",
  "limite_operacion": 50000,
  "es_principal": false
}
```

Monedas disponibles segun el enum backend actual: `ARS`, `USD` y `PUNTOS`.

Roles en UI:

- `owner`, `admin` y `super_admin`: pueden ver y crear wallets de organizacion cuando tienen una organizacion en alcance.
- `soporte`: puede ver wallets de organizacion, pero no ve el boton de creacion.
- `cliente`: ve solo sus wallets de usuario. No ve secciones ni acciones de organizacion.

La pantalla muestra loading, error y empty states por seccion; cards con alias, tipo, `owner_type`, moneda, saldo, estado, limite por operacion, marca principal y fecha de creacion; y al crear invalida queries de `wallets` y `dashboard`.

### Movimientos UI

La ruta privada `/movimientos` muestra datos reales y permite operar sobre wallets segun el rol autenticado. La pantalla usa TanStack Query para movimientos y wallets, filtros client-side, React Hook Form + Zod para formularios y modales separados para creacion, detalle y reversa.

Endpoints consumidos:

- `GET /api/v1/movimientos?skip=0&limit=100`: lista movimientos visibles.
- `GET /api/v1/movimientos/{movimiento_id}`: disponible en API frontend para detalle puntual.
- `POST /api/v1/movimientos/deposito`
- `POST /api/v1/movimientos/retiro`
- `POST /api/v1/movimientos/transferencia`
- `POST /api/v1/movimientos/pago`
- `POST /api/v1/movimientos/pago-organizacion`
- `POST /api/v1/movimientos/cashback`
- `POST /api/v1/movimientos/ajuste-admin`
- `POST /api/v1/movimientos/{movimiento_id}/reversa`
- `GET /api/v1/wallets`
- `GET /api/v1/wallets/organizacion`

Operaciones soportadas desde UI:

- `owner`, `admin` y `super_admin`: deposito, retiro, transferencia, pago a organizacion, cashback, ajuste admin y reversa de movimientos aprobados.
- `soporte`: consulta movimientos, sin acciones de creacion ni reversa.
- `cliente`: ve sus movimientos y solo puede iniciar `pago-organizacion`; con el contrato actual no puede listar wallets de organizacion, por lo que el formulario permite ingresar el ID destino manualmente.

Campos principales:

- Deposito y cashback acreditan `wallet_destino_id`.
- Retiro debita `wallet_origen_id`.
- Transferencia y pago a organizacion usan `wallet_origen_id`, `wallet_destino_id`, `monto`, `descripcion` y `referencia_externa`.
- Ajuste admin envia `wallet_id`, `operacion`, `monto`, `descripcion` y mapea la descripcion a `motivo`, requerido por backend.
- Reversa solicita `motivo_reversa` y crea un movimiento contable nuevo.

Limitaciones actuales:

- Los filtros de tipo, estado y busqueda por descripcion/referencia se aplican en frontend porque el backend todavia no expone esos query params.
- El listado carga hasta 100 movimientos recientes.
- La tabla muestra alias de wallets cuando la sesion tiene permiso para listarlas; si no, muestra el prefijo del ID.

### Notificaciones UI

La ruta privada `/notificaciones` muestra una bandeja real para consultar eventos internos, revisar el detalle y marcar notificaciones como leidas. El Topbar consume el contador de no leidas y muestra un badge cuando hay pendientes.

Endpoints consumidos:

- `GET /api/v1/notificaciones?skip=0&limit=100`: lista la bandeja visible para el usuario autenticado.
- `GET /api/v1/notificaciones/no-leidas/count`: obtiene el contador para la pagina, dashboard y Topbar.
- `PATCH /api/v1/notificaciones/{notificacion_id}/leida`: marca una notificacion como leida.
- `PATCH /api/v1/notificaciones/marcar-todas-leidas`: marca todas las notificaciones visibles como leidas.
- `GET /api/v1/notificaciones/organizacion?skip=0&limit=200`: bandeja organizacional para roles administrativos.

Datos visibles:

- Titulo, mensaje, tipo, canal, fecha de creacion y estado leida/no leida.
- Estado de envio para canal `email`: enviada, pendiente o error.
- Detalle con `id`, fechas de creacion, lectura y envio, error de envio y metadata formateada.
- Filtros client-side por leida/no leida, tipo, canal y busqueda en titulo, mensaje o metadata.

Roles en UI:

- `cliente`: consulta y marca sus propias notificaciones.
- `owner`, `admin` y `super_admin`: consultan la bandeja visible y la vista de organizacion.
- `soporte`: consulta su bandeja visible; el endpoint de organizacion existe pero el backend actual lo restringe a administradores, por eso la pestaña de organizacion no se muestra.

Acciones disponibles:

- Marcar una notificacion individual como leida.
- Marcar todas las notificaciones visibles como leidas.
- Ver detalle sin modificar el estado.

Limitaciones actuales:

- Los filtros se aplican en frontend porque el backend todavia no expone query params de tipo, canal o lectura.
- La vista de organizacion replica el alcance real del backend: administradores ven notificaciones internas de la organizacion; clientes y soporte no acceden a ese endpoint.

### Branding UI

La ruta privada `/branding` permite consultar y editar el branding de la organizacion cuando el rol tiene permisos. La pantalla usa React Hook Form + Zod, TanStack Query, preview visual y restricciones por plan para white-label avanzado.

Endpoints consumidos:

- `GET /api/v1/organizaciones/me/branding`: obtiene identidad, colores, dominios, moneda, timezone y estado white-label.
- `PATCH /api/v1/organizaciones/me/branding`: actualiza el branding de la organizacion actual.
- `GET /api/v1/planes/organizacion/actual`: consulta si el plan permite `permite_white_label`.

Campos editables:

- Identidad: `nombre_comercial`, `logo_url`.
- Colores: `color_primario`, `color_secundario` en formato HEX.
- Configuracion regional: `moneda_default` (`ARS`, `USD`, `USDT`, `PUNTOS`) y `timezone`.
- White-label: `subdominio`, `dominio_personalizado`, `permite_white_label_activo`.

Roles en UI:

- `owner`, `admin` y `super_admin`: pueden editar branding.
- `soporte`: puede ver branding, sin editar.
- `cliente`: ve mensaje sin permisos.

Reglas por plan:

- Si `plan.permite_white_label=false`, la UI bloquea `dominio_personalizado` y `permite_white_label_activo`.
- `subdominio` queda habilitado para roles editores porque el backend lo permite en cualquier plan.
- Al guardar, se invalidan branding, dashboard y planes; tambien se actualizan `--color-primary` y `--color-secondary` para reflejar los colores sin esperar recarga.

### Planes UI

La ruta privada `/planes` muestra el plan actual cuando el backend lo permite y una grilla de planes disponibles con limites y features comerciales.

Endpoints consumidos:

- `GET /api/v1/planes`: lista los planes activos disponibles.
- `GET /api/v1/planes/organizacion/actual`: obtiene el plan asignado a la organizacion actual.

Datos visibles:

- Plan actual, codigo, precio mensual y estado.
- Limites de usuarios, wallets y movimientos mensuales.
- Features: webhooks y white-label.
- Grilla comparativa de `Free`, `Starter`, `Pro` y `Enterprise`.
- CTA deshabilitado como `Proximamente`, porque no hay flujo frontend de cambio de plan en esta fase.

Roles en UI:

- `owner`, `admin` y `super_admin`: ven plan actual y catalogo de planes.
- `soporte`: ve catalogo de planes; el plan actual queda indicado como restringido porque el backend actual limita ese endpoint a roles administrativos.
- `cliente`: ve mensaje sin permisos para limites comerciales.

Limitaciones actuales:

- No se implementa cambio de plan desde frontend. El backend tiene endpoint administrativo de cambio, pero queda fuera de esta fase.
- La moneda del precio comercial se muestra en USD segun los planes base actuales.

### Usuarios UI

La ruta privada `/usuarios` permite administrar usuarios de la organizacion con TanStack Query, filtros client-side y modales con React Hook Form + Zod. La ruta esta lazy-loaded y el sidebar solo muestra la entrada cuando el rol puede consultar el endpoint real.

Endpoints consumidos:

- `GET /api/v1/usuarios`: lista usuarios visibles segun el alcance del usuario autenticado.
- `POST /api/v1/usuarios`: crea usuarios dentro de la organizacion actual.
- `PATCH /api/v1/usuarios/{usuario_id}` con `{ "rol": "admin" }`: cambia rol usando el endpoint general existente.
- `PATCH /api/v1/usuarios/{usuario_id}` con `{ "es_activo": true }`: activa o inactiva usuarios usando el endpoint general existente.
- `GET /api/v1/auth/me`: mantiene el usuario actual para permisos visuales.

Roles en UI:

- `owner`: puede ver, crear usuarios y cambiar rol/estado de usuarios de su organizacion, excepto a si mismo y usuarios `super_admin`.
- `admin`: puede ver, crear y gestionar usuarios, pero no modifica usuarios `owner`, `super_admin` ni a si mismo.
- `super_admin`: puede ver y gestionar usuarios visibles por backend, pero la UI de organizacion no permite crear ni asignar `super_admin`.
- `soporte`: no ve la entrada en sidebar porque el backend actual restringe `GET /api/v1/usuarios` a roles administrativos.
- `cliente`: no accede utilmente a la pantalla.

Reglas y limitaciones actuales:

- La creacion desde UI solo permite roles `admin`, `soporte` y `cliente`.
- El cambio de rol solo permite `owner`, `admin`, `soporte` y `cliente`; `super_admin` no se asigna desde el panel de organizacion.
- El backend no tiene sub-endpoints `/rol` o `/estado`; ambos cambios usan `PATCH /api/v1/usuarios/{usuario_id}`.
- El backend actual no expone un enum `estado` de usuario. La UI mapea `es_activo=true` a `activo` y `es_activo=false` a `inactivo`; `suspendido` solo se muestra si aparece un `bloqueado_hasta` futuro, pero no se puede setear desde esta pantalla.
- `UsuarioResponse` no expone fecha de creacion; la tabla muestra la columna solo si el backend incorpora un campo compatible en el futuro.
- Un `super_admin` sin organizacion en sesion puede listar o modificar segun backend, pero no ve el boton de creacion porque el formulario no incluye selector de organizacion.

### Integraciones UI

La ruta privada `/integraciones` deja de ser placeholder y permite gestionar API Keys, Webhooks y deliveries desde tabs independientes. La pantalla usa TanStack Query por panel, React Hook Form + Zod para formularios y respeta el plan actual consultando `GET /api/v1/planes/organizacion/actual`.

Endpoints consumidos:

- `GET /api/v1/integraciones/api-keys`
- `POST /api/v1/integraciones/api-keys`
- `DELETE /api/v1/integraciones/api-keys/{api_key_id}`
- `GET /api/v1/integraciones/webhooks`
- `POST /api/v1/integraciones/webhooks`
- `PATCH /api/v1/integraciones/webhooks/{webhook_id}`
- `DELETE /api/v1/integraciones/webhooks/{webhook_id}`
- `GET /api/v1/integraciones/webhooks/deliveries?skip=0&limit=100`
- `POST /api/v1/integraciones/webhooks/deliveries/{delivery_id}/reenviar`
- `GET /api/v1/planes/organizacion/actual`

API Keys:

- La tabla muestra `nombre`, `key_prefix`, scopes, estado, ultimo uso y fecha de creacion.
- La key real solo aparece en el modal posterior a la creacion y no se guarda en `localStorage` ni estado global.
- El boton de copiado usa `navigator.clipboard` y muestra feedback local.
- `owner`, `admin` y `super_admin` pueden crear y revocar; `soporte` solo ve la UI si el backend permite listar; `cliente` ve mensaje sin permisos.

Webhooks:

- El formulario pide `nombre`, `url`, `eventos`, `secret` y estado activo.
- El backend actual exige `secret` al crear y no lo devuelve; la UI no lo muestra luego ni lo incluye en tablas.
- Si el plan actual tiene `permite_webhooks=false`, la pantalla muestra "Tu plan actual no incluye webhooks." y deshabilita acciones de creacion/edicion.
- La tabla permite activar/pausar con `PATCH` y eliminar/desactivar con `DELETE` cuando el rol y el plan lo permiten.

Deliveries:

- La tabla muestra evento, status, `status_code`, intentos, fechas, error y accion de reenvio.
- Solo se habilita reenviar deliveries `fallido` o `pendiente`, usando `POST /api/v1/integraciones/webhooks/deliveries/{delivery_id}/reenviar`.
- Un fallo cargando deliveries no rompe las tabs de API Keys o Webhooks.

### Recompensas UI

La ruta privada `/recompensas` permite administrar loyalty y store credit desde el frontend. La feature vive en `src/features/recompensas`, usa Axios centralizado, TanStack Query por panel, React Hook Form + Zod para formularios y carga lazy desde el router.

Endpoints consumidos:

- `GET /api/v1/recompensas/reglas`
- `POST /api/v1/recompensas/reglas`
- `GET /api/v1/recompensas/reglas/{regla_id}`
- `PATCH /api/v1/recompensas/reglas/{regla_id}`
- `POST /api/v1/recompensas/simular`
- `POST /api/v1/recompensas/aplicar`
- `GET /api/v1/recompensas/aplicaciones?skip=0&limit=100`
- `GET /api/v1/recompensas/aplicaciones/me?skip=0&limit=100`

Roles en UI:

- `owner`, `admin` y `super_admin`: ven reglas, simulador, aplicacion manual y aplicaciones; pueden crear/editar reglas y aplicar recompensas.
- `soporte`: ve reglas, simulador y aplicaciones; no ve acciones de creacion, edicion ni aplicacion manual.
- `cliente`: ve solo `Mis recompensas`, con totales por moneda calculados client-side.

Reglas:

- El formulario permite configurar `cashback`, `puntos` o `credito_tienda`, estado `activa`, `inactiva` o `pausada`, moneda `ARS`, `USD` o `PUNTOS`, porcentaje, monto fijo, minimos, topes, acumulabilidad y vigencia.
- La UI valida que exista porcentaje o monto fijo y que `fecha_fin` sea posterior a `fecha_inicio`.
- Al guardar se invalidan queries de recompensas para refrescar listados.

Simulador:

- Permite ingresar `monto_compra`, seleccionar una regla opcional o filtrar por tipo.
- Muestra si aplica, monto de compra, monto de recompensa, moneda y motivo devuelto por backend.

Aplicacion manual:

- Disponible para roles administrativos.
- Solicita `usuario_id`, `wallet_destino_id`, `monto_compra`, regla opcional, `referencia_externa` y metadata JSON opcional.
- Al aplicar invalida recompensas, movimientos, wallets y dashboard para reflejar la acreditacion.

Vista cliente:

- Consume `/recompensas/aplicaciones/me`.
- Muestra recompensas recibidas, total acumulado por moneda y estados loading/error/empty propios.

### Ecommerce UI

La ruta privada `/ecommerce` permite visualizar y auditar ordenes recibidas desde tiendas externas. La feature vive en `src/features/ecommerce`, usa Axios centralizado, TanStack Query, filtros client-side y carga lazy desde el router.

Roles en UI:

- `owner`, `admin` y `super_admin`: ven resumen, curl de prueba, tabla de ordenes y detalle; tambien pueden gestionar API Keys desde `/integraciones`.
- `soporte`: ve la auditoria ecommerce en modo lectura, sin acciones de gestion de API Keys.
- `cliente`: no ve Ecommerce en el sidebar y recibe un estado sin permisos si intenta acceder directo.

Endpoints consumidos:

- `GET /api/v1/ecommerce/orders?skip=0&limit=100`
- `GET /api/v1/ecommerce/orders/{event_id}`
- `POST /api/v1/ext/ecommerce/order-paid` queda documentado como endpoint externo para tiendas con API Key.

Flujo de prueba:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid \
  -H "X-API-Key: wsk_test_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "proveedor": "generic",
    "external_order_id": "order-1001",
    "customer_email": "cliente@demo.com",
    "customer_name": "Cliente Demo",
    "amount": 20000,
    "currency": "ARS",
    "metadata": {
      "source": "tienda-demo"
    }
  }'
```

La API Key debe incluir `ecommerce:write`; la consulta visual requiere usuario JWT con permisos de lectura. Si hay regla activa, el flujo crea o reutiliza cliente y wallet, aplica cashback/store credit, genera movimiento, registra auditoria y permite seguir la aplicacion desde `/recompensas`. Los errores de procesamiento quedan visibles en tabla y modal junto con el `raw_payload`.

### Ecommerce E2E

Validacion manual recomendada con backend y frontend activos:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
npm run dev
python scripts/reset_local_db.py --yes
```

Confirmar servicios:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/docs
```

El reset imprime la API Key real solo cuando la crea en una base limpia:

```text
API Key real creada por primera vez: wsk_test_xxxxx
```

Curl Unix/macOS:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid \
  -H "X-API-Key: $API_KEY_ECOMMERCE_DEMO" \
  -H "Content-Type: application/json" \
  -d '{
    "proveedor": "generic",
    "external_order_id": "order-e2e-001",
    "customer_email": "cliente@demo.com",
    "customer_name": "Cliente Demo",
    "amount": 20000,
    "currency": "ARS",
    "metadata": { "source": "manual-e2e" }
  }'
```

Curl Windows PowerShell:

```powershell
$apiKey = "wsk_test_xxxxx"
@'
{"proveedor":"generic","external_order_id":"order-e2e-001","customer_email":"cliente@demo.com","customer_name":"Cliente Demo","amount":20000,"currency":"ARS","metadata":{"source":"manual-e2e"}}
'@ | Set-Content .\order-paid.json -Encoding utf8
curl.exe -X POST "http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid" -H "X-API-Key: $apiKey" -H "Content-Type: application/json" --data-binary "@order-paid.json"
```

Resultados esperados:

- Primer envio de `order-e2e-001`: `201`, `event.procesado=true`, `recompensa_aplicada_id` presente y movimiento `cashback`/`credito_tienda` creado.
- Repetir `order-e2e-001`: `409` con `La orden ya fue procesada.`; no duplica recompensa ni movimiento.
- Enviar `order-e2e-new-client` con `nuevo-cliente-ecommerce@example.com`: crea usuario `cliente`, wallet principal y recompensa si la regla demo aplica.
- Enviar una orden con `amount=500`: queda `procesado=true`, sin recompensa y con `error_procesamiento="No hay regla de recompensa aplicable"`.

Donde ver los resultados:

- `/ecommerce`: ordenes recibidas, estado, errores, `recompensa_aplicada_id`, filtros y modal con `raw_payload`.
- `/recompensas`: aplicacion de recompensa con referencia `ecommerce:{event_id}`.
- `/movimientos`: movimiento creado como `Recompensa ecommerce: Cashback Demo 10%`.
- `/notificaciones`: notificacion `Recompensa recibida` para el cliente.
- `/usuarios`: cliente auto-creado si se uso un email nuevo.
- Login `cliente@demo.com`: dashboard con saldo actualizado y `/recompensas` con `Mis recompensas`.

### Developer Portal

La ruta privada `/developer` documenta el uso tecnico de integraciones externas. Es visible en el sidebar para `owner`, `admin`, `soporte` y `super_admin`; el rol `cliente` no ve la entrada y recibe un estado sin permisos si intenta acceder directo.

Contenido incluido:

- Introduccion a Wallet SaaS como infraestructura.
- Autenticacion externa con `X-API-Key`.
- Tabla de scopes: `wallets:read`, `wallets:write`, `movimientos:read`, `movimientos:write`, `ecommerce:read`, `ecommerce:write`, `usuarios:read`, `usuarios:write`, `webhooks:read`, `webhooks:write`.
- Endpoints externos: `GET /api/v1/ext/wallets/{wallet_id}`, `POST /api/v1/ext/movimientos/deposito`, `POST /api/v1/ext/movimientos/cashback`, `GET /api/v1/ext/movimientos`, `POST /api/v1/ext/ecommerce/order-paid`.
- Ecommerce Integration: compra pagada externa, deduplicacion por `external_order_id`, scopes, ejemplo curl y link interno a `/ecommerce`.
- Recompensas API con JWT: reglas, simulacion, aplicacion manual y consulta de aplicaciones quedan documentadas como endpoints internos.
- Eventos webhook: `wallet.creada`, `movimiento.creado`, `movimiento.revertido`, `pago_organizacion.creado`, `ecommerce.order_paid`, `ecommerce.order_processed`, `ecommerce.order_failed`, `recompensa.aplicada`, `notificacion.creada`, `organizacion.suspendida`.
- Headers de firma: `X-Wallet-Signature`, `X-Wallet-Event`, `X-Wallet-Delivery-Id`.
- Sandbox local con usuarios demo por rol.

Ejemplos curl principales:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ext/movimientos/deposito \
  -H "X-API-Key: wsk_test_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{ "wallet_destino_id": "...", "monto": 1000, "descripcion": "Carga externa" }'

curl -X POST http://127.0.0.1:8000/api/v1/ext/movimientos/cashback \
  -H "X-API-Key: wsk_test_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{ "wallet_destino_id": "...", "monto": 250, "descripcion": "Cashback compra" }'

curl -X GET http://127.0.0.1:8000/api/v1/ext/movimientos \
  -H "X-API-Key: wsk_test_xxxxx"
```

Flujo recomendado para pruebas manuales:

1. Ejecutar `python scripts/reset_local_db.py --yes`.
2. Levantar backend con `uvicorn app.main:app --reload`.
3. Levantar frontend con `npm run dev`.
4. Iniciar sesion como `owner@demo.com`, `admin@demo.com`, `soporte@demo.com` o `superadmin@demo.com`.
5. Entrar a `/developer` y revisar API Keys, scopes, webhooks, HMAC y sandbox.
6. Iniciar sesion como `cliente@demo.com` y confirmar que Developer no aparece en el sidebar.

### Validacion E2E Integraciones

Validacion ejecutada el 2026-05-16 con backend activo en `http://127.0.0.1:8000` y frontend Vite en `http://127.0.0.1:5173`.

Servicios y CORS:

- `GET /health`, `/docs` y `/openapi.json` respondieron OK.
- El origen `http://127.0.0.1:5173` paso preflight y requests reales contra `/api/v1`.
- No se agrego CORS temporal. Para FASE 14.8.2 conviene mover origins a `.env`, porque hoy estan hardcodeados en backend.

Flujo probado:

- Alta desde `/onboarding` de `Demo Integraciones E2E` con slug `demo-integraciones-e2e-[timestamp]` y owner `owner-integraciones-[timestamp]@example.com`.
- Sesion owner cargada en navegador real para `/integraciones`.
- Usuarios `soporte` y `cliente` creados para validar restricciones.

API Keys:

- Owner creo `Key E2E` con scopes `wallets:read`, `movimientos:read` y `movimientos:write`.
- El backend devolvio la key real solo en creacion; luego el listado mostro `key_prefix`.
- Despues de recargar `/integraciones`, la key real no reaparecio en DOM, `localStorage` ni consola; tampoco se expuso `key_hash`.
- Revocacion validada con `DELETE /api/v1/integraciones/api-keys/{id}` y estado final `Revocada`.
- El copiado con `navigator.clipboard` quedo bloqueado en Chrome headless; se mantiene como dependiente del permiso del navegador.

Webhooks Free/Pro:

- En plan Free, la UI mostro `Tu plan actual no incluye webhooks` y el boton de creacion quedo deshabilitado.
- Submit forzado contra backend respondio `403` con `El plan free no permite webhooks.`
- Para validar Pro se cambio el plan de la organizacion por SQL directo de E2E, ya que no existe flujo UI de cambio de plan.
- En Pro, la UI habilito `Crear webhook`; se creo `Webhook E2E` contra `https://example.com/webhook-test` con eventos `movimiento.creado` y `pago_organizacion.creado`.
- El listado de webhooks mostro nombre, URL, eventos y activo; no expuso `secret` ni `secret_encrypted`.

Deliveries:

- Se genero un movimiento de deposito para disparar `movimiento.creado`.
- El delivery se creo y quedo `fallido` por resolucion DNS de `example.com` en el entorno local, con `intentos=1`.
- Reenvio manual validado: el endpoint respondio OK, paso por `pendiente` y luego fallo nuevamente por la misma causa externa, con `intentos=2`.

Roles:

- `owner`: puede crear/revocar API Keys, crear webhooks en Pro y reenviar deliveries permitidos.
- `soporte`: backend respondio `403` para API Keys, creacion de webhooks y reenvio/listado de deliveries; la UI no muestra acciones de creacion para este rol y debe presentar el error claro del backend cuando intenta consultar endpoints restringidos.
- `cliente`: backend respondio `403` en endpoints de integraciones; la UI bloquea el acceso util con mensaje sin permisos.

Seguridad de secretos:

- No se encontro API Key real ni webhook secret en `localStorage`.
- No se imprimieron secretos en consola; solo aparecieron mensajes de Vite/React DevTools.
- Las tablas no muestran secretos completos: API Keys usan `key_prefix` y Webhooks no renderizan secrets.

Observaciones pendientes:

- No hay UI para cambiar plan; el paso Free -> Pro se hizo por base de datos para esta validacion.
- Chrome headless no confirmo el cierre del modal de API Key por click aunque la recarga verifico que la key real no persiste ni vuelve a mostrarse.

### Limpieza tecnica FASE 14.8.2

Configuracion y limpieza:

- CORS quedo configurable con `CORS_ORIGINS` en `.env`, parseado como CSV desde `settings.CORS_ORIGINS`.
- `.env.example` documenta `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5177`.
- `.gitignore` cubre caches Python, `.pytest_cache/`, `.env`, `.env.local`, `node_modules/`, `dist/`, `.vite/`, logs y `.codex_tmp/`.
- Se elimino `app/apps/auth/models.py` porque solo reexportaba `Usuario` y no tenia imports consumidores.
- Se elimino `src/shared/hooks/useDebounce.js` porque no tenia consumidores.
- Se quitaron aliases API no usados en integraciones y planes.

Frontend:

- Las rutas privadas principales usan `React.lazy` + `Suspense` con `LoadingScreen`: dashboard, wallets, movimientos, notificaciones, branding, planes, integraciones, recompensas, ecommerce, developer y usuarios.
- El build quedo dividido por pagina; el chunk inicial bajo a ~496 kB y desaparecio el warning de Vite por chunk mayor a 500 kB.
- Las dependencias frontend actuales estan en uso: React, React DOM, React Router, Axios, TanStack Query, Zustand, React Hook Form, Zod, resolvers, Tailwind, ESLint y Vite.
- Se reviso seguridad local: el store de auth persiste solo token/user; API Keys y webhook secrets viven solo en formularios/modales y no se guardan en storage global.
- Las tablas usan contenedores `overflow-x-auto` y los modales tienen ancho maximo responsivo, por lo que mobile mantiene scroll horizontal contenido sin romper el layout de pagina.

Backend:

- La estructura modular mantiene separacion `models/services/routes/schemas` por app.
- No quedan imports a `app.apps.auth.models`; el modelo fuente de usuario es `app.apps.usuarios.models.Usuario`.
- Dependencias backend auditadas: se mantienen paquetes usados por FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, hashing, Postgres, tests, webhooks HTTP y cifrado.
- `python-multipart` y `fastapi-mail` no se agregan porque esta base no usa uploads/form-data ni FastAPI-Mail; email se implementa con `smtplib`.
- La compatibilidad de decrypt legacy de webhooks se conserva para no invalidar secrets existentes.

Recomendaciones para produccion:

- Mover auth a cookies HttpOnly/SameSite y rotacion de refresh tokens.
- Definir `CORS_ORIGINS` por ambiente, sin comodines.
- Configurar `SECRET_KEY` fuerte y rotacion controlada para claves/firmas.
- Servir frontend build desde CDN o servidor estatico con cache headers.
- Mantener `node_modules/`, `dist/`, caches y archivos temporales fuera del artefacto versionado.
