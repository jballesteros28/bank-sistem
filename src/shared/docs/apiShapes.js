/**
 * @typedef {Object} Usuario
 * @property {string} id
 * @property {string} nombre
 * @property {string} email
 * @property {"super_admin"|"owner"|"admin"|"soporte"|"cliente"} rol
 * @property {string|null} organizacion_id
 */

/**
 * @typedef {Object} Organizacion
 * @property {string} id
 * @property {string} nombre
 * @property {string} slug
 * @property {string} email_contacto
 * @property {string|null} plan_id
 * @property {"activa"|"inactiva"|"suspendida"} estado
 */

/**
 * @typedef {Object} Wallet
 * @property {string} id
 * @property {string|null} alias
 * @property {"usuario"|"organizacion"} owner_type
 * @property {string|null} usuario_id
 * @property {string|null} organizacion_owner_id
 * @property {string} organizacion_id
 * @property {"ARS"|"USD"|"PUNTOS"} moneda
 * @property {string} saldo
 * @property {"activa"|"inactiva"|"congelada"|"cerrada"} estado
 */

/**
 * @typedef {Object} Movimiento
 * @property {string} id
 * @property {string|null} wallet_origen_id
 * @property {string|null} wallet_destino_id
 * @property {string} organizacion_id
 * @property {string} monto
 * @property {"ARS"|"USD"|"PUNTOS"} moneda
 * @property {"deposito"|"retiro"|"transferencia"|"pago"|"cashback"|"ajuste_admin"|"reversa"} tipo
 * @property {"aprobada"|"pendiente"|"rechazada"|"cancelada"|"revertida"} estado
 */

/**
 * @typedef {Object} Plan
 * @property {string} id
 * @property {string} nombre
 * @property {string} codigo
 * @property {number|null} limite_usuarios
 * @property {number|null} limite_wallets
 * @property {number|null} limite_movimientos_mes
 * @property {boolean} permite_webhooks
 * @property {boolean} permite_white_label
 */

/**
 * @typedef {Object} Notificacion
 * @property {string} id
 * @property {string|null} usuario_id
 * @property {string} organizacion_id
 * @property {string} tipo
 * @property {"interna"|"email"} canal
 * @property {string} titulo
 * @property {string} mensaje
 * @property {boolean} leida
 */

/**
 * @typedef {Object} ApiKey
 * @property {string} id
 * @property {string} organizacion_id
 * @property {string} nombre
 * @property {string} key_prefix
 * @property {string[]} scopes
 * @property {boolean} activa
 */

/**
 * @typedef {Object} Webhook
 * @property {string} id
 * @property {string} organizacion_id
 * @property {string} nombre
 * @property {string} url
 * @property {string[]} eventos
 * @property {boolean} activo
 */

export const apiShapes = {};
