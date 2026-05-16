import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { createUsuario, usuariosQueryKeys } from "../api";
import { createUserRoleOptions, createUserSchema } from "../schemas";

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

function toPayload(values) {
  return {
    nombre: values.nombre.trim(),
    email: values.email.trim().toLowerCase(),
    password: values.password,
    rol: values.rol,
  };
}

export function CreateUserForm({ onCreated, onCancel }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      nombre: "",
      email: "",
      password: "",
      rol: "cliente",
    },
  });

  const mutation = useMutation({
    mutationFn: (values) => createUsuario(toPayload(values)),
    onSuccess: (usuario) => {
      queryClient.invalidateQueries({ queryKey: usuariosQueryKeys.all });
      showToast({
        title: "Usuario creado",
        message: `${usuario.nombre} quedo disponible en la organizacion.`,
      });
      reset();
      onCreated?.(usuario);
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
    if (mutation.isPending) {
      return;
    }
    mutation.mutate(values);
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Nombre" placeholder="Maria Gomez" error={errors.nombre?.message} {...register("nombre")} />
      <Input label="Email" type="email" placeholder="maria@example.com" error={errors.email?.message} {...register("email")} />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        error={errors.password?.message}
        {...register("password")}
      />
      <SelectField label="Rol" error={errors.rol?.message} {...register("rol")}>
        {createUserRoleOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </SelectField>
      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button type="submit" icon={UserPlus} loading={mutation.isPending}>
          Crear usuario
        </Button>
      </div>
    </form>
  );
}
