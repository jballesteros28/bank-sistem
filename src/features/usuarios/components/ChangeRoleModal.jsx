import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Modal } from "../../../shared/components/ui/Modal";
import { humanizeRole } from "../../../shared/utils/formatters";
import { canChangeUserRole, isAdmin, isOwner, isSuperAdmin } from "../../../shared/utils/roles";
import { updateUsuarioRol, usuariosQueryKeys } from "../api";
import { changeRoleOptions, changeRoleSchema } from "../schemas";
import { UserRoleBadge } from "./UserRoleBadge";

function SelectField({ label, error, children, ...props }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select
        className={[
          "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
          error ? "border-rose-300" : "border-slate-200",
        ].join(" ")}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}

function getInitialRole(usuario) {
  return changeRoleOptions.some((option) => option.value === usuario?.rol) ? usuario.rol : "cliente";
}

function getAllowedRoleOptions(currentUser) {
  if (isSuperAdmin(currentUser) || isOwner(currentUser)) {
    return changeRoleOptions;
  }
  if (isAdmin(currentUser)) {
    return changeRoleOptions.filter((option) => option.value !== "owner");
  }
  return [];
}

export function ChangeRoleModal({ usuario, currentUser, onClose }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const open = Boolean(usuario);
  const allowedRoleOptions = getAllowedRoleOptions(currentUser);
  const hasPermission = canChangeUserRole(currentUser, usuario);

  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(changeRoleSchema),
    defaultValues: {
      rol: getInitialRole(usuario),
    },
  });

  useEffect(() => {
    reset({ rol: getInitialRole(usuario) });
  }, [reset, usuario]);

  const selectedRole = useWatch({ control, name: "rol" });
  const isSameRole = selectedRole === usuario?.rol;

  const mutation = useMutation({
    mutationFn: (values) => updateUsuarioRol(usuario.id, { rol: values.rol }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: usuariosQueryKeys.all });
      showToast({
        title: "Rol actualizado",
        message: `${updated.nombre} ahora tiene rol ${humanizeRole(updated.rol)}.`,
      });
      onClose?.();
    },
    onError: (error) => {
      const validationErrors = getApiValidationErrors(error);
      Object.entries(validationErrors).forEach(([field, message]) => {
        setError(field, { message });
      });
      setError("root", { message: getApiErrorMessage(error) });
    },
  });

  const onSubmit = (values) => {
    if (mutation.isPending || !hasPermission || isSameRole) {
      return;
    }
    mutation.mutate(values);
  };

  return (
    <Modal open={open} title="Cambiar rol" onClose={onClose}>
      {usuario ? (
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-950">{usuario.nombre}</p>
            <p className="mt-1 text-sm text-slate-500">{usuario.email}</p>
            <div className="mt-3">
              <UserRoleBadge rol={usuario.rol} />
            </div>
          </div>
          {hasPermission ? (
            <SelectField label="Nuevo rol" error={errors.rol?.message} {...register("rol")}>
              {allowedRoleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </SelectField>
          ) : (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700">
              No tenes permisos para modificar el rol de este usuario.
            </p>
          )}
          {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
              Cancelar
            </Button>
            <Button type="submit" icon={ShieldCheck} loading={mutation.isPending} disabled={!hasPermission || isSameRole}>
              Guardar rol
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  );
}
