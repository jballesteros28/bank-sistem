import { z } from "zod";

export const organizationWalletTypeOptions = [
  { value: "empresa", label: "Empresa" },
  { value: "operativa", label: "Operativa" },
  { value: "caja", label: "Caja" },
  { value: "recompensas", label: "Recompensas" },
];

export const organizationWalletCurrencyOptions = [
  { value: "ARS", label: "ARS" },
  { value: "USD", label: "USD" },
  { value: "PUNTOS", label: "Puntos" },
];

const optionalPositiveNumber = z.preprocess((value) => {
  if (value === "" || value === null || value === undefined || Number.isNaN(value)) {
    return undefined;
  }
  if (typeof value === "string") {
    const parsed = Number(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : value;
  }
  return value;
}, z.number({ error: "Ingresa un limite valido." }).positive("El limite debe ser mayor a 0.").optional());

export const organizationWalletSchema = z.object({
  alias: z.string().trim().min(3, "El alias debe tener al menos 3 caracteres.").max(80, "El alias no puede superar 80 caracteres."),
  tipo: z.enum(["empresa", "operativa", "caja", "recompensas"], {
    error: "Selecciona un tipo valido.",
  }),
  moneda: z.enum(["ARS", "USD", "PUNTOS"], {
    error: "Selecciona una moneda valida.",
  }),
  limite_operacion: optionalPositiveNumber,
  es_principal: z.boolean().optional(),
});
