import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { createRewardRule, rewardQueryKeys, updateRewardRule } from "../api";
import { rewardCurrencyOptions, rewardRuleSchema, rewardStatusOptions, rewardTypeOptions } from "../schemas";

const selectClasses =
  "block h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20";

function valueOrEmpty(value) {
  return value === null || value === undefined ? "" : value;
}

function toDatetimeLocal(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 16);
}

function toIsoDateTime(value) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function buildDefaultValues(rule) {
  return {
    nombre: rule?.nombre || "",
    descripcion: rule?.descripcion || "",
    tipo: rule?.tipo || "cashback",
    estado: rule?.estado || "activa",
    porcentaje_cashback: valueOrEmpty(rule?.porcentaje_cashback),
    monto_fijo: valueOrEmpty(rule?.monto_fijo),
    moneda_recompensa: rule?.moneda_recompensa || "ARS",
    monto_minimo_compra: valueOrEmpty(rule?.monto_minimo_compra),
    monto_maximo_recompensa: valueOrEmpty(rule?.monto_maximo_recompensa),
    acumulable: rule?.acumulable ?? true,
    fecha_inicio: toDatetimeLocal(rule?.fecha_inicio),
    fecha_fin: toDatetimeLocal(rule?.fecha_fin),
  };
}

function buildPayload(values) {
  return {
    nombre: values.nombre.trim(),
    descripcion: values.descripcion || null,
    tipo: values.tipo,
    estado: values.estado || "activa",
    porcentaje_cashback: values.porcentaje_cashback ?? null,
    monto_fijo: values.monto_fijo ?? null,
    moneda_recompensa: values.moneda_recompensa,
    monto_minimo_compra: values.monto_minimo_compra ?? null,
    monto_maximo_recompensa: values.monto_maximo_recompensa ?? null,
    acumulable: values.acumulable,
    fecha_inicio: toIsoDateTime(values.fecha_inicio),
    fecha_fin: toIsoDateTime(values.fecha_fin),
  };
}

function SelectField({ label, error, children, ...props }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select className={[selectClasses, error ? "border-rose-300" : ""].filter(Boolean).join(" ")} {...props}>
        {children}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}

async function saveRule(rule, values) {
  const payload = buildPayload(values);

  if (rule?.id) {
    return updateRewardRule(rule.id, payload);
  }

  const { estado, ...createPayload } = payload;
  const created = await createRewardRule(createPayload);
  if (estado && estado !== "activa") {
    return updateRewardRule(created.id, { estado });
  }
  return created;
}

export function RewardRuleForm({ rule, onSaved, onCancel }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isEditing = Boolean(rule?.id);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(rewardRuleSchema),
    defaultValues: buildDefaultValues(rule),
  });

  useEffect(() => {
    reset(buildDefaultValues(rule));
  }, [reset, rule]);

  const mutation = useMutation({
    mutationFn: (values) => saveRule(rule, values),
    onSuccess: (savedRule) => {
      queryClient.invalidateQueries({ queryKey: rewardQueryKeys.all });
      showToast({
        title: isEditing ? "Regla actualizada" : "Regla creada",
        message: "Los cambios de recompensas quedaron guardados.",
      });
      onSaved?.(savedRule);
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
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Nombre" placeholder="Cashback Demo 10%" error={errors.nombre?.message} {...register("nombre")} />
        <SelectField label="Tipo" error={errors.tipo?.message} {...register("tipo")}>
          {rewardTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectField>
      </div>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-slate-700">Descripcion</span>
        <textarea
          className="block min-h-24 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
          placeholder="Opcional"
          {...register("descripcion")}
        />
        {errors.descripcion?.message ? <span className="block text-xs font-medium text-rose-600">{errors.descripcion.message}</span> : null}
      </label>

      <div className="grid gap-4 sm:grid-cols-3">
        <SelectField label="Estado" error={errors.estado?.message} {...register("estado")}>
          {rewardStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectField>
        <Input
          label="Porcentaje"
          inputMode="decimal"
          placeholder="10"
          hint="Usa porcentaje o monto fijo."
          error={errors.porcentaje_cashback?.message}
          {...register("porcentaje_cashback")}
        />
        <Input
          label="Monto fijo"
          inputMode="decimal"
          placeholder="500"
          hint="Puede quedar vacio si hay porcentaje."
          error={errors.monto_fijo?.message}
          {...register("monto_fijo")}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <SelectField label="Moneda recompensa" error={errors.moneda_recompensa?.message} {...register("moneda_recompensa")}>
          {rewardCurrencyOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectField>
        <Input
          label="Compra minima"
          inputMode="decimal"
          placeholder="0"
          error={errors.monto_minimo_compra?.message}
          {...register("monto_minimo_compra")}
        />
        <Input
          label="Tope recompensa"
          inputMode="decimal"
          placeholder="2000"
          error={errors.monto_maximo_recompensa?.message}
          {...register("monto_maximo_recompensa")}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Fecha inicio" type="datetime-local" error={errors.fecha_inicio?.message} {...register("fecha_inicio")} />
        <Input label="Fecha fin" type="datetime-local" error={errors.fecha_fin?.message} {...register("fecha_fin")} />
      </div>

      <label className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
        <input
          className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
          type="checkbox"
          {...register("acumulable")}
        />
        <span>
          <span className="block font-medium text-slate-800">Acumulable</span>
          <span className="mt-0.5 block text-slate-500">Permite combinar esta regla con otras promociones internas.</span>
        </span>
      </label>
      {errors.acumulable?.message ? <p className="text-xs font-medium text-rose-600">{errors.acumulable.message}</p> : null}

      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button type="submit" icon={Save} loading={mutation.isPending}>
          {isEditing ? "Guardar cambios" : "Crear regla"}
        </Button>
      </div>
    </form>
  );
}
