import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { Controller, useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { Modal } from "../../../shared/components/ui/Modal";
import { createApiKey, integrationsQueryKeys } from "../api";
import { apiKeySchema } from "../schemas";
import { ScopesSelector } from "./ScopesSelector";

function toPayload(values) {
  return {
    nombre: values.nombre.trim(),
    scopes: values.scopes,
  };
}

export function ApiKeyCreateModal({ open, onClose, onCreated }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(apiKeySchema),
    defaultValues: {
      nombre: "",
      scopes: ["wallets:read"],
    },
  });

  const mutation = useMutation({
    mutationFn: (values) => createApiKey(toPayload(values)),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.all });
      showToast({
        title: "API Key creada",
        message: "La key quedo activa para esta organizacion.",
      });
      reset();
      onCreated?.(created);
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
    <Modal open={open} title="Crear API Key" onClose={onClose}>
      <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
        <Input label="Nombre" placeholder="ERP produccion" error={errors.nombre?.message} {...register("nombre")} />
        <Controller
          control={control}
          name="scopes"
          render={({ field }) => <ScopesSelector value={field.value} onChange={field.onChange} error={errors.scopes?.message} />}
        />
        {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="submit" icon={KeyRound} loading={mutation.isPending}>
            Crear API Key
          </Button>
        </div>
      </form>
    </Modal>
  );
}
