import { z } from "zod";

export const API_KEY_SCOPE_OPTIONS = [
  { value: "wallets:read", label: "Wallets lectura", description: "Consultar wallets visibles para la organizacion." },
  { value: "wallets:write", label: "Wallets escritura", description: "Crear o modificar wallets mediante API externa." },
  { value: "movimientos:read", label: "Movimientos lectura", description: "Consultar movimientos externos." },
  { value: "movimientos:write", label: "Movimientos escritura", description: "Crear operaciones habilitadas por API Key." },
  { value: "usuarios:read", label: "Usuarios lectura", description: "Consultar informacion de usuarios cuando exista endpoint externo." },
  { value: "usuarios:write", label: "Usuarios escritura", description: "Gestionar usuarios cuando exista endpoint externo." },
  { value: "webhooks:read", label: "Webhooks lectura", description: "Consultar webhooks y deliveries." },
  { value: "webhooks:write", label: "Webhooks escritura", description: "Administrar webhooks desde integraciones externas." },
];

export const WEBHOOK_EVENT_OPTIONS = [
  { value: "wallet.creada", label: "Wallet creada" },
  { value: "movimiento.creado", label: "Movimiento creado" },
  { value: "movimiento.revertido", label: "Movimiento revertido" },
  { value: "pago_organizacion.creado", label: "Pago a organizacion creado" },
  { value: "recompensa.aplicada", label: "Recompensa aplicada" },
  { value: "notificacion.creada", label: "Notificacion creada" },
  { value: "organizacion.suspendida", label: "Organizacion suspendida" },
];

const apiKeyScopeValues = API_KEY_SCOPE_OPTIONS.map((option) => option.value);
const webhookEventValues = WEBHOOK_EVENT_OPTIONS.map((option) => option.value);

const nameSchema = z
  .string()
  .trim()
  .min(2, "El nombre debe tener al menos 2 caracteres.")
  .max(120, "El nombre no puede superar 120 caracteres.");

export const apiKeySchema = z.object({
  nombre: nameSchema,
  scopes: z.array(z.enum(apiKeyScopeValues, { error: "Selecciona un scope valido." })).min(1, "Selecciona al menos un scope."),
});

export const webhookSchema = z.object({
  nombre: nameSchema,
  url: z
    .string()
    .trim()
    .url("Ingresa una URL valida.")
    .refine((value) => value.startsWith("http://") || value.startsWith("https://"), "La URL debe usar http o https.")
    .max(500, "La URL no puede superar 500 caracteres."),
  eventos: z
    .array(z.enum(webhookEventValues, { error: "Selecciona un evento valido." }))
    .min(1, "Selecciona al menos un evento."),
  activo: z.boolean(),
  secret: z
    .string()
    .trim()
    .min(16, "El secret debe tener al menos 16 caracteres.")
    .max(255, "El secret no puede superar 255 caracteres."),
});
