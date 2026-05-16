import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("Ingresa un email valido."),
  password: z.string().min(8, "La password debe tener al menos 8 caracteres."),
});
