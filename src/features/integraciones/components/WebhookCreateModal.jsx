import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RadioTower } from "lucide-react";
import { Controller, useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { Modal } from "../../../shared/components/ui/Modal";
import { createWebhook, integrationsQueryKeys, updateWebhook } from "../api";
import { webhookSchema } from "../schemas";
import { WebhookEventsSelector } from "./WebhookEventsSelector";

function toCreatePayload(values) {
  return {
    nombre: values.nombre.trim(),
    url: values.url.trim(),
    eventos: values.eventos,
    secret: values.secret.trim(),
  };
}

async function createWebhookWithActiveState(values) {
  const created = await createWebhook(toCreatePayload(values));
  if (values.activo === false) {
    return updateWebhook(created.id, { activo: false });
  }
  return created;
}

export function WebhookCreateModal({ open, onClose, onCreated }) {
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
    resolver: zodResolver(webhookSchema),
    defaultValues: {
      nombre: "",
      url: "",
      eventos: ["movimiento.creado"],
      activo: true,
      secret: "",
    },
  });

  const mutation = useMutation({
    mutationFn: createWebhookWithActiveState,
    onSuccess: (webhook) => {
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.all });
      showToast({
        title: "Webhook creado",
        message: "El endpoint quedo disponible para los eventos seleccionados.",
      });
      reset();
      onCreated?.(webhook);
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
    <Modal open={open} title="Crear webhook" onClose={onClose}>
      <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
        <Input label="Nombre" placeholder="ERP eventos" error={errors.nombre?.message} {...register("nombre")} />
        <Input label="URL" placeholder="https://example.com/webhooks/wallet" error={errors.url?.message} {...register("url")} />
        <Input
          label="Secret HMAC"
          type="password"
          autoComplete="off"
          placeholder="Minimo 16 caracteres"
          error={errors.secret?.message}
          hint="El backend lo usa para firmar deliveries y no lo devuelve en listados."
          {...register("secret")}
        />
        <Controller
          control={control}
          name="eventos"
          render={({ field }) => <WebhookEventsSelector value={field.value} onChange={field.onChange} error={errors.eventos?.message} />}
        />
        <label className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
          <input
            className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
            type="checkbox"
            {...register("activo")}
          />
          <span>
            <span className="block font-medium text-slate-800">Crear activo</span>
            <span className="mt-0.5 block text-slate-500">Si lo desmarcas, se crea y se pausa inmediatamente.</span>
          </span>
        </label>
        {errors.activo?.message ? <p className="text-xs font-medium text-rose-600">{errors.activo.message}</p> : null}
        {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="submit" icon={RadioTower} loading={mutation.isPending}>
            Crear webhook
          </Button>
        </div>
      </form>
    </Modal>
  );
}
