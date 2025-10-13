# 🏦 Sistema Bancario Backend — FastAPI + PostgreSQL + MongoDB + Docker

[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-brightgreen?logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

### 📘 Descripción

**Sistema Bancario Backend** desarrollado con **FastAPI**, **PostgreSQL**, **MongoDB** y **Docker**.  
Diseñado con arquitectura modular, autenticación JWT, logs en Mongo, notificaciones por correo y trazabilidad completa.

> 💡 Proyecto educativo y demostrativo de arquitectura backend profesional con Python.

---

### 🧠 Tecnologías

- **FastAPI** – Framework backend asíncrono.
- **SQLAlchemy 2.0** – ORM para PostgreSQL.
- **Motor + MongoDB** – Persistencia de logs y auditoría.
- **JWT (JSON Web Tokens)** – Autenticación y roles.
- **FastAPI-Mail** – Envío real de correos con plantillas HTML.
- **Docker Compose** – Entorno completo de despliegue.
- **Alembic** – Migraciones automáticas.
- **Pytest + Requests** – Testing real y simulado.

---

### ⚙️ Instalación local (sin Docker)

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/sistema-bancario-backend.git
cd sistema-bancario-backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env
cp .env.example .env

# 5. Ejecutar el servidor
uvicorn main:app --reload
Acceder a la API → http://localhost:8000/docs

🐳 Ejecución con Docker (recomendado)
bash
Copiar código
# Build + iniciar servicios (PostgreSQL + Mongo + API)
docker-compose up -d --build

# Detener servicios
docker-compose down
Acceso → http://localhost:8000/docs

🔐 Variables de entorno (.env.example)
ini
Copiar código
# PostgreSQL
POSTGRES_DB=sistema_bancario
POSTGRES_USER=usuario
POSTGRES_PASSWORD=contraseña
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=banco_logs

# Seguridad JWT
SECRET_KEY=clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=clave
MAIL_FROM=tu_email@gmail.com
📂 Estructura del proyecto
pgsql
Copiar código
sistema-bancario-backend/
├── core/
├── database/
├── models/
├── schemas/
├── services/
├── routes/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
🧪 Testing
Ejecutar los tests manuales:

bash
Copiar código
python tests/test_admin/test_summary_logs.py
O con pytest:

bash
Copiar código
pytest -v
🛡️ Roles y permisos
Rol	Permisos
Admin	CRUD completo, reportes, logs
Cliente	Operaciones de cuenta y transferencias
Anónimo	Registro y login

🧾 Licencia
Este proyecto fue desarrollado por Juan David Ballesteros
🧑‍💻 Full Stack Developer | Especializado en FastAPI, React y arquitectura escalable

Licencia: MIT

⭐ Si te gustó este proyecto, dejá una star en GitHub
y seguime para más contenido sobre desarrollo Full Stack Python 🚀

yaml
Copiar código

---

## 🔐 Funcionalidades principales

### ✅ Autenticación
- Registro y login con JWT
- Validaciones estrictas de email y contraseña
- Roles (`cliente`, `admin`, `soporte`)

### 👥 Usuarios y cuentas
- Crear/ver cuentas bancarias
- Consultar saldo y estado
- Cambiar contraseña y editar perfil
- Congelar/reactivar cuentas (admin)

### 💸 Transacciones
- Transferencias seguras entre cuentas
- Ver historial (como emisor o receptor)
- Validaciones de saldo, estado y pertenencia

### 🛠️ Administración (solo para admins)
- Listar y gestionar usuarios
- Cambiar roles
- Congelar cuentas
- Consultar logs persistentes (MongoDB)
- Reportes: transacciones por fecha, estado de cuentas

---

## 🔔 Notificaciones (fase activa)

En esta etapa se implementa el módulo de notificaciones para auditar y alertar al usuario:

- 📩 Simulación/envío de emails
- 📦 Registro de eventos importantes en MongoDB (login fallido, errores, transferencias)
- 🔔 (Opcional) WebSocket para notificaciones en tiempo real

---

## 🧪 Próximos pasos

- Implementar sistema de notificaciones email/alerta
- Agregar WebSocket para push en tiempo real
- Crear frontend con React clásico
- Tests unitarios (`pytest`)
- Dockerización + despliegue

---

## 🧠 Autor

**Juan David Ballesteros**  
Desarrollador Full Stack | Backend con Python, FastAPI y bases de datos relacionales y no relacionales.  
🔗 [LinkedIn](https://www.linkedin.com/in/juan-david-ballesteros-413350260)

---

## 📜 Licencia

MIT © 2025 - Juan David Ballesteros