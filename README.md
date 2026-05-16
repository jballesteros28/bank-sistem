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

Frontend:

```bash
npm install
npm run dev
npm run lint
npm run build
npm run preview
```

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
- `POST /api/v1/integraciones/api-keys`
- `GET /api/v1/integraciones/webhooks`
- `POST /api/v1/integraciones/webhooks/deliveries/{delivery_id}/reenviar`
- `GET /api/v1/ext/wallets/{wallet_id}`
- `POST /api/v1/ext/movimientos/deposito`
- `POST /api/v1/ext/movimientos/cashback`

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
- Privadas: `/dashboard`, `/wallets`, `/movimientos`, `/notificaciones`, `/branding`, `/planes`, `/integraciones`

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

- No hay credenciales fijas versionadas para el frontend.
- Para probar manualmente, crear una organizacion nueva desde `/onboarding` y usar el email/password del owner creado.

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

- Si el navegador muestra `Network Error` pero `curl`/PowerShell contra la API funciona, revisar CORS. El backend permite `localhost` y `127.0.0.1` para Vite en `5173` y `5174`.
- Si una ruta privada vuelve a `/login`, revisar que exista `wallet_saas_token` y que `GET /api/v1/auth/me` devuelva `200`.
- Si el token esta vencido o malformado, el comportamiento esperado es `401`, limpieza de storage y redireccion a `/login`.
- Si Vite cambia de puerto, agregar ese origin a `allow_origins` o iniciar Vite explicitamente con `--port 5173`/`5174`.

Validacion local completada:

- `GET /health`, `/docs` y `/openapi.json`: OK.
- UI E2E con Chrome headless/CDP: OK.
- `npm run lint`: OK.
- `npm run build`: OK.
- `python -m pytest -q`: OK.

### Dashboard Owner

El dashboard privado de `/dashboard` muestra informacion real para usuarios `owner` y `admin` autenticados. Tambien degrada por seccion si un endpoint no aplica al rol actual, por ejemplo `soporte` o `super_admin` sin organizacion asociada.

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
- Si el usuario tiene rol `cliente`, se muestra una pantalla de preparacion para un dashboard especifico futuro.
- Si un endpoint falla por permisos o falta de organizacion, el dashboard conserva las demas secciones y muestra el error puntual.

Validacion FASE 14.3:

- UI E2E owner: onboarding, login, dashboard real, refresh, logout y token invalido OK.
- Dashboard owner mostro `Free`, limite de 3 wallets, `Wallet empresa`, saldo ARS, movimientos recientes y notificaciones no leidas.
- Endpoints del dashboard respondieron `200` durante la prueba UI.

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
- `cliente`: no puede listar ni crear wallets de organizacion; la seccion aparece bloqueada y conserva la lista de wallets de usuario.

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
- `cliente`: ve sus movimientos y puede iniciar pago a organizacion; con el contrato actual no puede listar wallets de organizacion, por lo que el formulario permite ingresar el ID destino si no hay wallets seleccionables.

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
