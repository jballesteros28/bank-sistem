import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { Input } from "../../../shared/components/ui/Input";
import { planQueryKeys } from "../../planes/api";
import { brandingQueryKeys, updateBranding } from "../api";
import { brandingCurrencyOptions, brandingSchema, timezoneOptions } from "../schemas";
import { BrandingPreview } from "./BrandingPreview";
import { ColorInput } from "./ColorInput";
import { DomainSettingsCard } from "./DomainSettingsCard";

function applyBrandingVariables(branding) {
  const root = document.documentElement;
  root.style.setProperty("--color-primary", branding?.color_primario || "#0f766e");
  root.style.setProperty("--color-secondary", branding?.color_secundario || "#2563eb");
}

function emptyToNull(value) {
  return value === "" || value === undefined ? null : value;
}

function toFormValues(branding) {
  return {
    nombre_comercial: branding?.nombre_comercial || "",
    logo_url: branding?.logo_url || "",
    color_primario: branding?.color_primario || "#0f766e",
    color_secundario: branding?.color_secundario || "#2563eb",
    subdominio: branding?.subdominio || "",
    dominio_personalizado: branding?.dominio_personalizado || "",
    moneda_default: branding?.moneda_default || "ARS",
    timezone: branding?.timezone || "America/Argentina/Buenos_Aires",
    permite_white_label_activo: Boolean(branding?.permite_white_label_activo),
  };
}

function toPayload(values, whiteLabelAllowed) {
  return {
    nombre_comercial: emptyToNull(values.nombre_comercial),
    logo_url: emptyToNull(values.logo_url),
    color_primario: emptyToNull(values.color_primario),
    color_secundario: emptyToNull(values.color_secundario),
    subdominio: emptyToNull(values.subdominio),
    dominio_personalizado: whiteLabelAllowed ? emptyToNull(values.dominio_personalizado) : null,
    moneda_default: values.moneda_default,
    timezone: values.timezone,
    permite_white_label_activo: whiteLabelAllowed ? Boolean(values.permite_white_label_activo) : false,
  };
}

function SelectField({ label, error, children, disabled = false, ...props }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select
        className={[
          "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500",
          error ? "border-rose-300" : "border-slate-200",
        ].join(" ")}
        disabled={disabled}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}

export function BrandingForm({ branding, plan, canEdit = false }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const whiteLabelAllowed = Boolean(plan?.permite_white_label);
  const disabled = !canEdit;

  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(brandingSchema),
    defaultValues: toFormValues(branding),
  });

  useEffect(() => {
    reset(toFormValues(branding));
  }, [branding, reset]);

  const values = useWatch({ control });
  const previewBranding = { ...branding, ...values };

  const mutation = useMutation({
    mutationFn: (formValues) => updateBranding(toPayload(formValues, whiteLabelAllowed)),
    onSuccess: (updatedBranding) => {
      applyBrandingVariables(updatedBranding);
      queryClient.invalidateQueries({ queryKey: brandingQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: planQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      reset(toFormValues(updatedBranding));
      showToast({
        title: "Branding actualizado",
        message: "La marca de la organizacion ya esta aplicada.",
      });
    },
    onError: (error) => {
      const validationErrors = getApiValidationErrors(error);
      Object.entries(validationErrors).forEach(([field, message]) => {
        setError(field, { message });
      });
      setError("root", { message: getApiErrorMessage(error) });
    },
  });

  const onSubmit = (formValues) => {
    if (!canEdit || mutation.isPending) {
      return;
    }
    mutation.mutate(formValues);
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader title="Identidad" description="Nombre comercial y logo publico de la organizacion." />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Nombre comercial" error={errors.nombre_comercial?.message} disabled={disabled} {...register("nombre_comercial")} />
            <Input label="Logo URL" error={errors.logo_url?.message} disabled={disabled} {...register("logo_url")} />
          </div>
        </Card>

        <Card>
          <CardHeader title="Colores" description="Variables visuales aplicadas al layout y componentes principales." />
          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              control={control}
              name="color_primario"
              render={({ field }) => (
                <ColorInput
                  label="Color primario"
                  error={errors.color_primario?.message}
                  disabled={disabled}
                  name={field.name}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
            <Controller
              control={control}
              name="color_secundario"
              render={({ field }) => (
                <ColorInput
                  label="Color secundario"
                  error={errors.color_secundario?.message}
                  disabled={disabled}
                  name={field.name}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </div>
        </Card>

        <Card>
          <CardHeader title="Configuracion regional" description="Moneda base y zona horaria de la organizacion." />
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField label="Moneda default" error={errors.moneda_default?.message} disabled={disabled} {...register("moneda_default")}>
              {brandingCurrencyOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </SelectField>
            <SelectField label="Timezone" error={errors.timezone?.message} disabled={disabled} {...register("timezone")}>
              {timezoneOptions.map((timezone) => (
                <option key={timezone} value={timezone}>
                  {timezone}
                </option>
              ))}
            </SelectField>
          </div>
        </Card>

        <DomainSettingsCard
          register={register}
          errors={errors}
          disabled={disabled}
          whiteLabelAllowed={whiteLabelAllowed}
          whiteLabelDisabled={!whiteLabelAllowed}
        />

        {errors.root?.message ? <ErrorState title="No se pudo guardar" message={errors.root.message} /> : null}
        {canEdit ? (
          <Button type="submit" icon={Save} loading={mutation.isPending}>
            Guardar branding
          </Button>
        ) : null}
      </form>
      <div className="xl:sticky xl:top-24 xl:self-start">
        <BrandingPreview branding={previewBranding} />
      </div>
    </div>
  );
}
