import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ToggleLeft } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Modal } from "../../../shared/components/ui/Modal";
import { canChangeUserStatus } from "../../../shared/utils/roles";
import { updateUsuarioEstado, usuariosQueryKeys } from "../api";
import { changeStatusSchema, getUsuarioStatus, userStatusOptions } from "../schemas";
import { UserStatusBadge } from "./UserStatusBadge";

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

function getEditableStatus(usuario) {
  return usuario?.es_activo === false ? "inactivo" : "activo";
}

export function ChangeStatusModal({ usuario, currentUser, onClose }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const open = Boolean(usuario);
  const hasPermission = canChangeUserStatus(currentUser, usuario);

  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(changeStatusSchema),
    defaultValues: {
      estado: getEditableStatus(usuario),
    },
  });

  useEffect(() => {
    reset({ estado: getEditableStatus(usuario) });
  }, [reset, usuario]);

  const selectedStatus = useWatch({ control, name: "estado" });
  const isSameStatus = selectedStatus === getEditableStatus(usuario);

  const mutation = useMutation({
    mutationFn: (values) => updateUsuarioEstado(usuario.id, { estado: values.estado }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: usuariosQueryKeys.all });
      showToast({
        title: "Estado actualizado",
        message: `${updated.nombre} quedo ${getUsuarioStatus(updated)}.`,
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
    if (mutation.isPending || !hasPermission || isSameStatus) {
      return;
    }
    mutation.mutate(values);
  };

  return (
    <Modal open={open} title="Cambiar estado" onClose={onClose}>
      {usuario ? (
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-950">{usuario.nombre}</p>
            <p className="mt-1 text-sm text-slate-500">{usuario.email}</p>
            <div className="mt-3">
              <UserStatusBadge usuario={usuario} />
            </div>
          </div>
          {hasPermission ? (
            <SelectField label="Nuevo estado" error={errors.estado?.message} {...register("estado")}>
              {userStatusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </SelectField>
          ) : (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700">
              No tenes permisos para modificar el estado de este usuario.
            </p>
          )}
          {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
              Cancelar
            </Button>
            <Button type="submit" icon={ToggleLeft} loading={mutation.isPending} disabled={!hasPermission || isSameStatus}>
              Guardar estado
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  );
}
