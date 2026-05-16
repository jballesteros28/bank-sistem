import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { createWalletOrganizacion, walletQueryKeys } from "../api";
import {
  organizationWalletCurrencyOptions,
  organizationWalletSchema,
  organizationWalletTypeOptions,
} from "../schemas";

function SelectField({ label, error, children, id, className = "", ...props }) {
  const inputId = id || props.name;
  const classes = [
    "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
    error ? "border-rose-300" : "border-slate-200",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <label className="block space-y-1.5" htmlFor={inputId}>
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select id={inputId} className={classes} {...props}>
        {children}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}

function toPayload(values) {
  const payload = {
    alias: values.alias.trim(),
    tipo: values.tipo,
    moneda: values.moneda,
    es_principal: Boolean(values.es_principal),
  };

  if (values.limite_operacion !== undefined) {
    payload.limite_operacion = values.limite_operacion;
  }

  return payload;
}

export function CreateOrganizationWalletForm({ onCreated, onCancel }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(organizationWalletSchema),
    defaultValues: {
      alias: "",
      tipo: "caja",
      moneda: "ARS",
      limite_operacion: "",
      es_principal: false,
    },
  });

  const mutation = useMutation({
    mutationFn: createWalletOrganizacion,
    onSuccess: (wallet) => {
      queryClient.invalidateQueries({ queryKey: walletQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      showToast({
        title: "Wallet creada",
        message: wallet?.alias ? `${wallet.alias} ya esta disponible.` : "La wallet de organizacion ya esta disponible.",
      });
      reset();
      onCreated?.(wallet);
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
    mutation.mutate(toPayload(values));
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Alias" error={errors.alias?.message} placeholder="Caja sucursal centro" {...register("alias")} />
      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Tipo" error={errors.tipo?.message} {...register("tipo")}>
          {organizationWalletTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectField>
        <SelectField label="Moneda" error={errors.moneda?.message} {...register("moneda")}>
          {organizationWalletCurrencyOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectField>
      </div>
      <Input
        label="Limite por operacion"
        error={errors.limite_operacion?.message}
        hint="Opcional"
        inputMode="decimal"
        placeholder="50000"
        {...register("limite_operacion")}
      />
      <label className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
        <input
          className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
          type="checkbox"
          {...register("es_principal")}
        />
        <span>
          <span className="block font-medium text-slate-800">Marcar como principal</span>
          <span className="mt-0.5 block text-slate-500">Solo puede existir una wallet principal activa por organizacion.</span>
        </span>
      </label>
      {errors.es_principal?.message ? <p className="text-xs font-medium text-rose-600">{errors.es_principal.message}</p> : null}
      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button type="submit" icon={Save} loading={mutation.isPending}>
          Crear wallet
        </Button>
      </div>
    </form>
  );
}
