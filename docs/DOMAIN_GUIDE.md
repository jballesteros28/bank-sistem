# Guia de dominio Wallet SaaS

## Conceptos

- **Cuenta**: concepto legacy del sistema bancario original. Sigue existiendo por compatibilidad en `/cuentas`, pero no es el lenguaje principal del producto.
- **Wallet**: concepto principal del SaaS. Internamente se persiste sobre la tabla `cuentas` durante esta etapa de migracion.
- **Transaccion**: concepto legacy asociado a `/transacciones`. Se conserva para clientes existentes.
- **Movimiento**: concepto principal para operaciones financieras de wallet. Internamente se persiste sobre la tabla `transacciones`.
- **Organizacion**: cliente SaaS o tenant. Agrupa usuarios, wallets y movimientos bajo aislamiento por `organizacion_id`.
- **Super admin**: administra la plataforma completa y puede operar transversalmente donde el dominio lo permita.
- **Owner**: usuario inicial de una organizacion registrada por onboarding. Administra su tenant y no tiene permisos globales.
- **Admin**: administra una organizacion especifica y queda limitado a su tenant.

## Reglas de dominio

- Todo dato operativo debe tener `organizacion_id`.
- No se confia en `organizacion_id` enviado por frontend; siempre se resuelve desde el usuario autenticado y su organizacion.
- El onboarding publico crea en una unica transaccion la organizacion, el usuario `owner` y la wallet principal.
- No se borran movimientos financieros.
- Las reversas crean movimientos inversos y marcan el movimiento original como revertido cuando corresponde.
- Las wallets cerradas o congeladas no pueden operar.
- Las operaciones entre wallets deben respetar moneda, saldo disponible y `limite_operacion` si existe.
- `/cuentas` y `/transacciones` son endpoints legacy y seran removidos en una version futura.

## Versionado

La API actual mantiene rutas sin prefijo para compatibilidad:

- `/wallets`
- `/movimientos`
- `/organizaciones`

El prefijo recomendado para la siguiente evolucion publica es:

- `/api/v1/wallets`
- `/api/v1/movimientos`
- `/api/v1/organizaciones`

La constante `API_V1_PREFIX = "/api/v1"` vive en `core/api.py`. En esta fase no se migran rutas para evitar cambios grandes de compatibilidad.
