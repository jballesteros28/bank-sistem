# 💸 Sistema Bancario Backend — FastAPI + PostgreSQL + MongoDB

Este es un backend completo y escalable para una aplicación de sistema bancario moderno. Desarrollado con FastAPI, PostgreSQL y MongoDB, incluye autenticación segura, gestión de usuarios y cuentas, transacciones bancarias, administración avanzada y trazabilidad completa del sistema.

---

## 🚀 Tecnologías utilizadas

- **⚙️ Backend:** FastAPI
- **🗃️ Base de datos relacional:** PostgreSQL con SQLAlchemy 2.0
- **📦 Base de datos NoSQL:** MongoDB (Motor) para logs y notificaciones
- **🔐 Seguridad:** JWT, Hashing, Roles, Middlewares personalizados
- **📁 Arquitectura:** Modular, desacoplada, profesional
- **📦 Validación:** Pydantic v2 con enums, restricciones y mensajes amigables

---

## 📁 Estructura principal del proyecto

sistema_bancario/
│
├── app/ # Lógica de negocio y rutas (auth, usuarios, admin, etc.)
├── core/ # Configuración general, seguridad, dependencias
├── models/ # Modelos ORM (SQLAlchemy)
├── schemas/ # Esquemas de entrada/salida (Pydantic)
├── services/ # Lógica desacoplada del negocio
├── database/ # Conexiones y migraciones (PostgreSQL + MongoDB)
├── tests/ # Pruebas unitarias (futuro)
├── main.py # Punto de entrada FastAPI
├── requirements.txt # Dependencias
└── .env # Variables de entorno (no incluido en Git)

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
🔗 [LinkedIn](https://www.linkedin.com/in/juan-david-ballesteros-bayona-413350260)

---

## 📜 Licencia

MIT © 2025 - Juan David Ballesteros
