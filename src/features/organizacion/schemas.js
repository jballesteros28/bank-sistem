import { z } from "zod";

const optionalText = (max) =>
  z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return value;
  }, z.string().trim().max(max, `No puede superar ${max} caracteres.`).optional());

const hexColor = z.preprocess((value) => {
  if (typeof value === "string" && value.trim() === "") {
    return undefined;
  }
  return value;
}, z.string().regex(/^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/, "Usa un color HEX valido.").optional());

export const brandingCurrencyOptions = [
  { value: "ARS", label: "ARS" },
  { value: "USD", label: "USD" },
  { value: "USDT", label: "USDT" },
  { value: "PUNTOS", label: "Puntos" },
];

export const timezoneOptions = [
  "America/Argentina/Buenos_Aires",
  "America/Buenos_Aires",
  "America/Sao_Paulo",
  "America/Santiago",
  "America/Mexico_City",
  "America/Bogota",
  "UTC",
];

export const brandingSchema = z.object({
  nombre_comercial: optionalText(150),
  logo_url: z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return value;
  }, z.url("Ingresa una URL valida.").max(500, "No puede superar 500 caracteres.").optional()),
  color_primario: hexColor,
  color_secundario: hexColor,
  subdominio: z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return typeof value === "string" ? value.toLowerCase().trim() : value;
  }, z.string().regex(/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/, "Usa minusculas, numeros y guiones.").optional()),
  dominio_personalizado: z.preprocess((value) => {
    if (typeof value === "string" && value.trim() === "") {
      return undefined;
    }
    return typeof value === "string" ? value.toLowerCase().trim() : value;
  }, z.string().regex(/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/, "Ingresa un dominio valido sin protocolo.").optional()),
  moneda_default: z.enum(["ARS", "USD", "USDT", "PUNTOS"], {
    error: "Selecciona una moneda valida.",
  }),
  timezone: z.string().trim().min(1, "Indica un timezone.").max(80, "No puede superar 80 caracteres."),
  permite_white_label_activo: z.boolean().optional(),
});
