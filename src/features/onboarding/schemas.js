import { z } from "zod";

export const onboardingSchema = z.object({
  organizacion: z.object({
    nombre: z.string().min(2, "Indica el nombre de la organizacion.").max(150),
    slug: z
      .string()
      .min(2, "Indica un slug valido.")
      .max(120)
      .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Usa minusculas, numeros y guiones."),
    email_contacto: z.email("Ingresa un email valido."),
  }),
  owner: z.object({
    nombre: z.string().min(2, "Indica el nombre del owner.").max(100),
    email: z.email("Ingresa un email valido."),
    password: z.string().min(8, "La password debe tener al menos 8 caracteres.").max(128),
  }),
});
