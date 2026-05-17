# Deployment

Esta guia deja el proyecto listo para correr fuera del entorno local. No cubre Docker ni el deploy cloud final.

## Ambientes

- `development`: defaults comodos para trabajar localmente.
- `testing`: usado por pytest con base aislada.
- `production`: exige configuracion explicita y segura para secretos, DB y CORS.

## Backend

Variables principales:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB_NAME
SECRET_KEY=generar-un-valor-largo-y-aleatorio-de-32-caracteres-o-mas
CORS_ORIGINS=https://wallet-demo.vercel.app
EMAILS_ENABLED=false
FRONTEND_URL=https://wallet-demo.vercel.app
BACKEND_URL=https://tu-backend-demo.onrender.com
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
python -m alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Para una primera demo en Render o Railway alcanza con `uvicorn`. Si luego se necesita un proceso manager, evaluar `gunicorn` con worker Uvicorn en una fase separada.

Health checks:

```bash
curl https://tu-backend-demo.onrender.com/health
curl https://tu-backend-demo.onrender.com/ready
```

`/health` valida que la app responde. `/ready` ejecuta un `SELECT 1` contra la DB y devuelve `503` si no esta disponible.

## Frontend

Variables Vite:

```env
VITE_API_BASE_URL=https://tu-backend-demo.onrender.com
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

El build genera `dist/`. No versionar `.env`, `.env.local` ni `dist/`.

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
