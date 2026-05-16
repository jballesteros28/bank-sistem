import { z } from "zod";

export const userRoleOptions = [
  { value: "owner", label: "Owner" },
  { value: "admin", label: "Admin" },
  { value: "soporte", label: "Soporte" },
  { value: "cliente", label: "Cliente" },
  { value: "super_admin", label: "Super admin" },
];

export const createUserRoleOptions = userRoleOptions.filter((option) =>
  ["admin", "soporte", "cliente"].includes(option.value),
);

export const changeRoleOptions = userRoleOptions.filter((option) => option.value !== "super_admin");

export const userStatusOptions = [
  { value: "activo", label: "Activo" },
  { value: "inactivo", label: "Inactivo" },
];

export const userStatusFilterOptions = [...userStatusOptions, { value: "suspendido", label: "Suspendido" }];

const createUserRoleValues = createUserRoleOptions.map((option) => option.value);
const changeRoleValues = changeRoleOptions.map((option) => option.value);
const statusValues = userStatusOptions.map((option) => option.value);

export const createUserSchema = z.object({
  nombre: z.string().trim().min(2, "El nombre debe tener al menos 2 caracteres.").max(100, "El nombre no puede superar 100 caracteres."),
  email: z.email("Ingresa un email valido."),
  password: z.string().min(8, "La password debe tener al menos 8 caracteres.").max(128, "La password no puede superar 128 caracteres."),
  rol: z.enum(createUserRoleValues, { error: "Selecciona un rol valido." }),
});

export const changeRoleSchema = z.object({
  rol: z.enum(changeRoleValues, { error: "Selecciona un rol valido." }),
});

export const changeStatusSchema = z.object({
  estado: z.enum(statusValues, { error: "Selecciona un estado valido." }),
});

export function getUsuarioStatus(usuario) {
  if (usuario?.estado) {
    return usuario.estado;
  }

  if (usuario?.bloqueado_hasta) {
    const blockedUntil = new Date(usuario.bloqueado_hasta);
    if (!Number.isNaN(blockedUntil.getTime()) && blockedUntil > new Date()) {
      return "suspendido";
    }
  }

  return usuario?.es_activo === false ? "inactivo" : "activo";
}

export function getUsuarioCreatedAt(usuario) {
  return usuario?.created_at || usuario?.createdAt || usuario?.creado_en || usuario?.fecha_creacion || null;
}
