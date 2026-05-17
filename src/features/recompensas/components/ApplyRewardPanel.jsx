import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Gift } from "lucide-react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { Input } from "../../../shared/components/ui/Input";
import { formatCurrency, formatNumber } from "../../../shared/utils/formatters";
import { movementQueryKeys } from "../../movimientos/api";
import { walletQueryKeys } from "../../wallets/api";
import { applyReward, getRewardRules, rewardQueryKeys } from "../api";
import { applyRewardSchema } from "../schemas";

function cleanPayload(values) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined && value !== ""));
}

function formatRewardValue(value, currency) {
  if (currency === "PUNTOS") {
    return `${formatNumber(value)} PUNTOS`;
  }
  return formatCurrency(value, currency);
}

function ApplyResult({ result }) {
  if (!result?.aplicacion) {
    return null;
  }

  const application = result.aplicacion;

  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
      <p className="text-sm font-semibold text-emerald-900">Recompensa aplicada</p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-emerald-700">Recompensa</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-950">
            {formatRewardValue(application.monto_recompensa, application.moneda_recompensa)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-emerald-700">Aplicacion</dt>
          <dd className="mt-1 font-mono text-xs text-slate-700">{application.id}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-normal text-emerald-700">Movimiento</dt>
          <dd className="mt-1 font-mono text-xs text-slate-700">{application.movimiento_id || result.movimiento?.id || "-"}</dd>
        </div>
      </dl>
    </div>
  );
}

export function ApplyRewardPanel({ user, canApply = false }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const organizationId = user?.organizacion_id || "global";

  const rulesQuery = useQuery({
    queryKey: rewardQueryKeys.rewardRules(organizationId),
    queryFn: () => getRewardRules(),
    enabled: canApply,
    retry: false,
  });

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(applyRewardSchema),
    defaultValues: {
      usuario_id: "",
      wallet_destino_id: "",
      monto_compra: "",
      regla_id: "",
      referencia_externa: "",
      metadata: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (values) => applyReward(cleanPayload(values)),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: rewardQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: movementQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: walletQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      showToast({
        title: "Recompensa aplicada",
        message: "La wallet del cliente fue acreditada correctamente.",
      });
      reset({
        usuario_id: "",
        wallet_destino_id: "",
        monto_compra: "",
        regla_id: "",
        referencia_externa: "",
        metadata: "",
      });
      return result;
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

  const rules = rulesQuery.data || [];

  return (
    <Card>
      <CardHeader title="Aplicar recompensa" description="Acredita manualmente una recompensa a la wallet de un cliente." />

      {!canApply ? (
        <EmptyState icon={Gift} title="Sin permisos" description="Tu rol no puede aplicar recompensas manualmente." />
      ) : (
        <div className="space-y-5">
          {rulesQuery.error ? (
            <ErrorState title="Reglas no disponibles" message={getApiErrorMessage(rulesQuery.error)} onRetry={() => rulesQuery.refetch()} />
          ) : null}
          {!rulesQuery.isLoading && !rulesQuery.error && !rules.length ? (
            <EmptyState icon={Gift} title="Sin reglas" description="Necesitas al menos una regla activa para aplicar recompensas." />
          ) : null}

          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Usuario ID" placeholder="UUID del cliente" error={errors.usuario_id?.message} {...register("usuario_id")} />
              <Input
                label="Wallet destino ID"
                placeholder="UUID de la wallet"
                error={errors.wallet_destino_id?.message}
                {...register("wallet_destino_id")}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
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
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Referencia externa"
                placeholder="orden-1001"
                error={errors.referencia_externa?.message}
                hint="Opcional"
                {...register("referencia_externa")}
              />
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Metadata JSON</span>
                <textarea
                  className="block min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                  placeholder='{"canal":"manual"}'
                  {...register("metadata")}
                />
                {errors.metadata?.message ? <span className="block text-xs font-medium text-rose-600">{errors.metadata.message}</span> : null}
              </label>
            </div>

            {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}

            <div className="flex justify-end">
              <Button type="submit" icon={Gift} loading={mutation.isPending}>
                Aplicar recompensa
              </Button>
            </div>
          </form>

          <ApplyResult result={mutation.data} />
        </div>
      )}
    </Card>
  );
}
