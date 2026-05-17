import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Calculator } from "lucide-react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { Input } from "../../../shared/components/ui/Input";
import { formatCurrency, formatNumber } from "../../../shared/utils/formatters";
import { getRewardRules, rewardQueryKeys, simulateReward } from "../api";
import { rewardTypeOptions, simulateRewardSchema } from "../schemas";

function cleanPayload(values) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined && value !== ""));
}

function formatRewardValue(value, currency) {
  if (!currency) {
    return "-";
  }
  if (currency === "PUNTOS") {
    return `${formatNumber(value)} PUNTOS`;
  }
  return formatCurrency(value, currency);
}

function ResultCard({ result }) {
  if (!result) {
    return null;
  }

  return (
    <div className={["rounded-lg border p-4", result.aplica ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"].join(" ")}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className={["text-sm font-semibold", result.aplica ? "text-emerald-900" : "text-amber-900"].join(" ")}>
            {result.aplica ? "Aplica" : "No aplica"}
          </p>
          <p className={["mt-1 text-sm", result.aplica ? "text-emerald-700" : "text-amber-700"].join(" ")}>{result.motivo}</p>
        </div>
        {result.nombre_regla ? <span className="text-sm font-medium text-slate-700">{result.nombre_regla}</span> : null}
      </div>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-slate-500">Compra</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-950">{formatNumber(result.monto_compra)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-slate-500">Recompensa</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-950">
            {formatRewardValue(result.monto_recompensa, result.moneda_recompensa)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-slate-500">Moneda</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-950">{result.moneda_recompensa || "-"}</dd>
        </div>
      </dl>
    </div>
  );
}

export function RewardSimulatorPanel({ user, canSimulate = true }) {
  const organizationId = user?.organizacion_id || "global";
  const rulesQuery = useQuery({
    queryKey: rewardQueryKeys.rewardRules(organizationId),
    queryFn: () => getRewardRules(),
    enabled: canSimulate,
    retry: false,
  });

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(simulateRewardSchema),
    defaultValues: {
      monto_compra: "",
      regla_id: "",
      tipo: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (values) => simulateReward(cleanPayload(values)),
    mutationKey: rewardQueryKeys.rewardSimulation(),
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

  const rules = rulesQuery.data || [];

  return (
    <Card>
      <CardHeader title="Simulador" description="Calcula si una compra dispararia cashback, puntos o credito interno." />

      {!canSimulate ? (
        <EmptyState icon={Calculator} title="Sin permisos" description="Tu rol no puede simular recompensas." />
      ) : (
        <div className="space-y-5">
          {rulesQuery.error ? (
            <ErrorState title="Reglas no disponibles" message={getApiErrorMessage(rulesQuery.error)} onRetry={() => rulesQuery.refetch()} />
          ) : null}
          {!rulesQuery.isLoading && !rulesQuery.error && !rules.length ? (
            <EmptyState icon={Calculator} title="Sin reglas para simular" description="Crea una regla activa o simula por tipo cuando exista configuracion." />
          ) : null}

          <form className="grid gap-4 lg:grid-cols-[1fr_1fr_auto]" onSubmit={handleSubmit(onSubmit)}>
            <Input label="Monto compra" inputMode="decimal" placeholder="20000" error={errors.monto_compra?.message} {...register("monto_compra")} />
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">Regla</span>
              <select
                className="block h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                disabled={rulesQuery.isLoading || Boolean(rulesQuery.error)}
                {...register("regla_id")}
              >
                <option value="">{rulesQuery.isLoading ? "Cargando reglas..." : "Automatica"}</option>
                {rules.map((rule) => (
                  <option key={rule.id} value={rule.id}>
                    {rule.nombre}
                  </option>
                ))}
              </select>
              {errors.regla_id?.message ? <span className="block text-xs font-medium text-rose-600">{errors.regla_id.message}</span> : null}
            </label>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">Tipo</span>
              <select
                className="block h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                {...register("tipo")}
              >
                <option value="">Cualquiera</option>
                {rewardTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {errors.tipo?.message ? <span className="block text-xs font-medium text-rose-600">{errors.tipo.message}</span> : null}
            </label>
            <div className="lg:col-span-3 flex justify-end">
              <Button type="submit" icon={Calculator} loading={mutation.isPending}>
                Simular
              </Button>
            </div>
          </form>

          {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
          <ResultCard result={mutation.data} />
        </div>
      )}
    </Card>
  );
}
