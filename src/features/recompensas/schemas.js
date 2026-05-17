import { z } from "zod";

export const rewardTypeOptions = [
  { value: "cashback", label: "Cashback" },
  { value: "puntos", label: "Puntos" },
  { value: "credito_tienda", label: "Credito tienda" },
];

export const rewardStatusOptions = [
  { value: "activa", label: "Activa" },
  { value: "inactiva", label: "Inactiva" },
  { value: "pausada", label: "Pausada" },
];

export const rewardCurrencyOptions = [
  { value: "ARS", label: "ARS" },
  { value: "USD", label: "USD" },
  { value: "PUNTOS", label: "PUNTOS" },
];

const rewardTypeValues = rewardTypeOptions.map((option) => option.value);
const rewardStatusValues = rewardStatusOptions.map((option) => option.value);
const rewardCurrencyValues = rewardCurrencyOptions.map((option) => option.value);

const optionalText = (max = 255) =>
  z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return value;
  }, z.string().trim().max(max, `No puede superar ${max} caracteres.`).optional());

const nullableText = (max = 255) =>
  z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return null;
    }
    return value;
  }, z.string().trim().max(max, `No puede superar ${max} caracteres.`).nullable().optional());

const numberFromInput = (schema) =>
  z.preprocess((value) => {
    if (value === "" || value === null || value === undefined || Number.isNaN(value)) {
      return undefined;
    }
    if (typeof value === "string") {
      const parsed = Number(value.replace(",", "."));
      return Number.isFinite(parsed) ? parsed : value;
    }
    return value;
  }, schema);

const positiveAmount = numberFromInput(
  z.number({ error: "Ingresa un monto valido." }).positive("El monto debe ser mayor a 0."),
);

const optionalPositiveAmount = numberFromInput(
  z.number({ error: "Ingresa un monto valido." }).positive("El monto debe ser mayor a 0.").optional(),
);

const optionalNonNegativeAmount = numberFromInput(
  z.number({ error: "Ingresa un monto valido." }).min(0, "El monto debe ser mayor o igual a 0.").optional(),
);

const optionalPercentage = numberFromInput(
  z
    .number({ error: "Ingresa un porcentaje valido." })
    .positive("El porcentaje debe ser mayor a 0.")
    .max(100, "El porcentaje no puede superar 100.")
    .optional(),
);

const optionalDate = z.preprocess((value) => {
  if (value === "" || value === null || value === undefined) {
    return undefined;
  }
  return value;
}, z.string().optional());

const metadataSchema = z.preprocess((value) => {
  if (value === "" || value === null || value === undefined) {
    return undefined;
  }
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return value;
    }
  }
  return value;
}, z.record(z.string(), z.any(), { error: "Ingresa un JSON valido." }).optional());

export const rewardRuleSchema = z
  .object({
    nombre: z
      .string()
      .trim()
      .min(2, "El nombre debe tener al menos 2 caracteres.")
      .max(120, "El nombre no puede superar 120 caracteres."),
    descripcion: nullableText(500),
    tipo: z.enum(rewardTypeValues, { error: "Selecciona un tipo valido." }),
    estado: z.enum(rewardStatusValues, { error: "Selecciona un estado valido." }).optional(),
    porcentaje_cashback: optionalPercentage,
    monto_fijo: optionalPositiveAmount,
    moneda_recompensa: z.enum(rewardCurrencyValues, { error: "Selecciona una moneda valida." }),
    monto_minimo_compra: optionalNonNegativeAmount,
    monto_maximo_recompensa: optionalPositiveAmount,
    acumulable: z.boolean(),
    fecha_inicio: optionalDate,
    fecha_fin: optionalDate,
  })
  .refine((values) => values.porcentaje_cashback !== undefined || values.monto_fijo !== undefined, {
    path: ["porcentaje_cashback"],
    message: "Indica un porcentaje o un monto fijo.",
  })
  .refine(
    (values) => {
      if (!values.fecha_inicio || !values.fecha_fin) {
        return true;
      }
      return new Date(values.fecha_fin).getTime() > new Date(values.fecha_inicio).getTime();
    },
    {
      path: ["fecha_fin"],
      message: "La fecha fin debe ser posterior a la fecha inicio.",
    },
  );

export const simulateRewardSchema = z.object({
  monto_compra: positiveAmount,
  regla_id: optionalText(80),
  tipo: z.preprocess((value) => (value === "" ? undefined : value), z.enum(rewardTypeValues).optional()),
});

export const applyRewardSchema = z.object({
  usuario_id: z.string().trim().min(1, "Ingresa el usuario."),
  wallet_destino_id: z.string().trim().min(1, "Ingresa la wallet destino."),
  monto_compra: positiveAmount,
  regla_id: optionalText(80),
  referencia_externa: optionalText(120),
  metadata: metadataSchema,
});

export function getRewardTypeLabel(type) {
  return rewardTypeOptions.find((option) => option.value === type)?.label || type || "-";
}

export function getRewardStatusLabel(status) {
  return rewardStatusOptions.find((option) => option.value === status)?.label || status || "-";
}
