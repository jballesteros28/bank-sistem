# bank-sistem. en produccion
# 🏦 Sistema Bancario Moderno — Full Stack App

Este proyecto es un sistema bancario profesional, moderno y escalable, diseñado con arquitectura modular. Permite gestionar usuarios, cuentas bancarias, transacciones y notificaciones con un enfoque seguro, eficiente y extensible.

## 🚀 Tecnologías utilizadas

### 🔧 Backend
- **FastAPI** — API REST rápida y moderna
- **SQLAlchemy 2.0** — ORM para modelado relacional
- **PostgreSQL** — Base de datos principal para operaciones bancarias
- **MongoDB** — Almacenamiento flexible para logs y notificaciones
- **Alembic** — Control de versiones para la base de datos
- **JWT** — Autenticación segura con tokens
- **Pydantic** — Validación de datos

### 🖥️ Frontend (en desarrollo)
- **React clásico** — Interfaz de usuario intuitiva y escalable
- **Axios** — Comunicación con la API
- **CSS clásico** — Estilado personalizado sin frameworks de UI

## 🧩 Módulos del sistema

- **Autenticación**: Registro, login, JWT, verificación de identidad
- **Usuarios**: Gestión de perfil, roles, activación/desactivación
- **Cuentas bancarias**: Apertura, saldo, cierre y tipos de cuenta
- **Transacciones**: Transferencias, historial, programaciones
- **Notificaciones**: Alertas por email o WebSocket (MongoDB)
- **Administración**: Monitoreo, control de usuarios y logs

## ⚙️ Estructura de carpetas

📦 sistema_bancario/
├── app/ # Rutas y controladores por módulo
├── core/ # Configuración y seguridad
├── models/ # Modelos de base de datos
├── schemas/ # Esquemas de validación (Pydantic)
├── services/ # Lógica de negocio
├── database/ # Conexiones PostgreSQL y MongoDB
├── tests/ # Pruebas unitarias
├── main.py # Punto de entrada de la API
└── .env # Variables de entorno

bash
Copiar
Editar

## 📦 Instalación rápida

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # en Linux/macOS
venv\Scripts\activate     # en Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
uvicorn main:app --reload
🔐 Endpoints clave
POST /auth/register → Crear nuevo usuario

POST /auth/login → Obtener token JWT

GET /auth/me → Ver usuario autenticado (requiere token)

📅 Próximas funcionalidades
Autenticación 2FA

Transacciones recurrentes

Reportes financieros avanzados

Frontend React + dashboard
