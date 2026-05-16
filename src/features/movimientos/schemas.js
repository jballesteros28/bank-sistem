import { z } from "zod";

const requiredWallet = z.string().min(1, "Selecciona una wallet.");

const amountSchema = z.preprocess((value) => {
  if (value === "" || value === null || value === undefined || Number.isNaN(value)) {
    return undefined;
  }
  if (typeof value === "string") {
    const parsed = Number(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : value;
  }
  return value;
}, z.number({ error: "Ingresa un monto valido." }).positive("El monto debe ser mayor a 0."));

const optionalText = (max = 255) =>
  z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return value;
  }, z.string().trim().max(max, `No puede superar ${max} caracteres.`).optional());

const baseMovementFields = {
  monto: amountSchema,
  descripcion: optionalText(255),
  referencia_externa: optionalText(120),
};

export const depositoSchema = z.object({
  wallet_destino_id: requiredWallet,
  ...baseMovementFields,
});

export const retiroSchema = z.object({
  wallet_origen_id: requiredWallet,
  ...baseMovementFields,
});

export const transferenciaSchema = z
  .object({
    wallet_origen_id: requiredWallet,
    wallet_destino_id: requiredWallet,
    ...baseMovementFields,
  })
  .refine((values) => values.wallet_origen_id !== values.wallet_destino_id, {
    path: ["wallet_destino_id"],
    message: "Origen y destino no pueden ser la misma wallet.",
  });

export const pagoOrganizacionSchema = transferenciaSchema;

export const cashbackSchema = z.object({
  wallet_destino_id: requiredWallet,
  monto: amountSchema,
  descripcion: optionalText(255),
});

export const ajusteAdminSchema = z.object({
  wallet_id: requiredWallet,
  operacion: z.enum(["credito", "debito"], {
    error: "Selecciona una operacion valida.",
  }),
  monto: amountSchema,
  descripcion: z.string().trim().min(3, "Indica una descripcion.").max(255, "No puede superar 255 caracteres."),
});

export const reversaSchema = z.object({
  motivo_reversa: z.string().trim().min(5, "Indica un motivo de al menos 5 caracteres.").max(255, "No puede superar 255 caracteres."),
});

export const movementSchemas = {
  deposito: depositoSchema,
  retiro: retiroSchema,
  transferencia: transferenciaSchema,
  pago_organizacion: pagoOrganizacionSchema,
  cashback: cashbackSchema,
  ajuste_admin: ajusteAdminSchema,
};
