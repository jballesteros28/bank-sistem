# Deployment

Esta guia cubre el deploy real recomendado con Railway para backend + PostgreSQL y Vercel para frontend. Tambien documenta el entorno local completo con Docker Compose.

## Ambientes

- `development`: defaults comodos para trabajar localmente.
- `testing`: usado por pytest con base aislada.
- `production`: exige configuracion explicita y segura para secretos, DB y CORS.

## Backend Railway

Variables principales:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB_NAME
SECRET_KEY=generar-un-valor-largo-y-aleatorio-de-32-caracteres-o-mas
CORS_ORIGINS=https://wallet-demo.vercel.app
EMAILS_ENABLED=false
FRONTEND_URL=https://wallet-demo.vercel.app
BACKEND_URL=https://wallet-saas-backend.up.railway.app
LOG_LEVEL=INFO
```

Reglas de produccion:

- `SECRET_KEY` no puede ser `change-me` ni un valor corto.
- `DATABASE_URL` debe estar definido.
- `CORS_ORIGINS` debe listar dominios reales separados por coma. No usar `*`.
- Para agregar un frontend, sumar su origen exacto, por ejemplo `https://wallet-demo.vercel.app`.
- `EMAILS_ENABLED=true` solo cuando SMTP este configurado correctamente.

Comandos recomendados:

```bash
sh scripts/docker_start.sh
```

Railway usa `Dockerfile.backend` y `railway.json`. El comando de arranque corre `python -m alembic upgrade head` y despues levanta Uvicorn en `PORT` con fallback local a `8000`.

Pasos Railway:

1. Crear un proyecto en Railway.
2. Agregar PostgreSQL administrado.
3. Crear el servicio backend desde el repositorio.
4. Confirmar que el builder use `Dockerfile.backend`; `railway.json` ya define el path.
5. Configurar las variables de entorno anteriores. `DATABASE_URL` debe venir del PostgreSQL de Railway.
6. Deployar backend y esperar que el healthcheck `/ready` quede verde.
7. Copiar la URL publica del backend para usarla en Vercel y en `BACKEND_URL`.

Health checks:

```bash
curl https://wallet-saas-backend.up.railway.app/health
curl https://wallet-saas-backend.up.railway.app/ready
```

`/health` valida que la app responde. `/ready` ejecuta un `SELECT 1` contra la DB y devuelve `503` si no esta disponible.

## Frontend Vercel

Variables Vite:

```env
VITE_API_BASE_URL=https://wallet-saas-backend.up.railway.app
VITE_API_PREFIX=/api/v1
VITE_APP_NAME=Wallet SaaS
```

En local usar:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Comandos:

```bash
npm install
npm run lint
npm run build
npm run preview
```

Pasos Vercel:

1. Deployar el backend primero y verificar `/ready`.
2. Crear el proyecto frontend en Vercel desde el mismo repositorio.
3. Configurar build command `npm run build` y output directory `dist`.
4. Configurar `VITE_API_BASE_URL` con la URL publica del backend Railway.
5. Configurar `VITE_API_PREFIX=/api/v1` y `VITE_APP_NAME=Wallet SaaS`.
6. Deployar frontend.
7. Volver a Railway y actualizar `CORS_ORIGINS` y `FRONTEND_URL` con el dominio final de Vercel; redeployar backend si Railway no reinicia automaticamente.

`vercel.json` reescribe `/(.*)` a `/index.html` para que rutas SPA como `/dashboard`, `/wallets` y `/ecommerce` funcionen al refrescar.

El build genera `dist/`. No versionar `.env`, `.env.local` ni `dist/`.

## Docker Local

El Compose local levanta PostgreSQL, backend FastAPI y frontend React servido por Nginx. Usa `ENVIRONMENT=development` para permitir secretos demo locales y no debe usarse como configuracion final de produccion sin cambios.

Servicios:

- `postgres`: PostgreSQL con volumen `postgres_data`.
- `backend`: FastAPI en `http://localhost:8000`, ejecuta migraciones con Alembic al iniciar.
- `frontend`: Nginx sirviendo el build Vite en `http://localhost:3000`.

Comandos:

```bash
docker compose build
docker compose up
```

En otra terminal, cargar datos demo cuando el backend este healthy:

```bash
docker compose exec backend python scripts/dev_seed.py
```

URLs:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

Reset completo del entorno Docker local:

```bash
docker compose down -v
docker compose up --build
docker compose exec backend python scripts/dev_seed.py
```

El seed no corre automaticamente para evitar datos demo en entornos equivocados.

Para produccion real:

- Usar `ENVIRONMENT=production`.
- Reemplazar `SECRET_KEY` por un secreto fuerte.
- Apuntar `DATABASE_URL` a PostgreSQL administrado o al servicio productivo real.
- Configurar `CORS_ORIGINS`, `FRONTEND_URL` y `BACKEND_URL` con dominios reales.
- No usar passwords demo de Compose.

## Scripts Locales

`scripts/dev_seed.py` y `scripts/reset_local_db.py` son solo para desarrollo. Ambos abortan con `ENVIRONMENT=production` y tambien frenan si `DATABASE_URL` no parece local. No usarlos contra una DB productiva.

## Seguridad Frontend

- Las API Keys reales se muestran solo al crearlas y no se guardan en `localStorage`.
- Los webhook secrets se envian al backend al crear webhooks y no se guardan en storage global.
- El JWT sigue en `localStorage` por ahora. TODO futuro: migrar autenticacion a cookies HttpOnly/SameSite antes de produccion real.

## Troubleshooting

CORS:

- Verificar que `CORS_ORIGINS` tenga el origen exacto del frontend, incluyendo protocolo.
- No incluir path. Correcto: `https://wallet-demo.vercel.app`.

DB connection:

- Confirmar host, puerto, usuario, password, nombre de base y SSL requerido por el proveedor.
- Revisar `/ready`: si devuelve `503`, el backend arranco pero no llega a DB.

401:

- Confirmar `SECRET_KEY` consistente entre procesos.
- Revisar que el frontend apunte al backend correcto con `VITE_API_BASE_URL`.
- Si hay token viejo en navegador, cerrar sesion o limpiar storage.

Migrations:

- Ejecutar `python -m alembic upgrade head` antes de abrir trafico.
- Si falta una tabla o columna, revisar `python -m alembic current`.

Vite env:

- Las variables deben empezar con `VITE_`.
- Cambios de `.env` requieren reiniciar `npm run dev` o reconstruir con `npm run build`.

Docker:

- Puertos ocupados: cambiar los mappings `3000:80`, `8000:8000` o `5432:5432` en `docker-compose.yml`.
- Docker Desktop en Windows: si `docker version` muestra `Access is denied` contra `C:\Users\<usuario>\.docker\config.json` o `//./pipe/docker_engine`, iniciar Docker Desktop, usar el contexto `desktop-linux` y ejecutar la terminal con permisos para acceder al daemon.
- `VITE_API_BASE_URL`: se hornea en el build del frontend; si cambia, reconstruir `frontend`.
- CORS: el backend local Docker permite `http://localhost:3000` y `http://127.0.0.1:3000`.
- Migraciones: el backend corre `python -m alembic upgrade head` al iniciar; revisar logs si `/ready` devuelve `503`.
- Postgres health: `backend` espera `pg_isready` antes de iniciar.
- PowerShell + curl: si un `POST` con JSON inline devuelve `422 json_invalid`, guardar el payload en un `.json` y usar `curl.exe --data-binary "@payload.json"` para evitar que PowerShell altere las comillas.
