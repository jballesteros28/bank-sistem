import { CreditCard } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { formatCurrency } from "../../../shared/utils/formatters";
import { PlanBadge } from "./PlanBadge";
import { PlanFeatureList } from "./PlanFeatureList";
import { PlanLimitsCard } from "./PlanLimitsCard";

function LoadingPlan() {
  return (
    <div className="space-y-4">
      <div className="h-8 w-40 animate-pulse rounded bg-slate-100" />
      <div className="h-16 animate-pulse rounded bg-slate-100" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="h-24 animate-pulse rounded bg-slate-100" />
        <div className="h-24 animate-pulse rounded bg-slate-100" />
        <div className="h-24 animate-pulse rounded bg-slate-100" />
      </div>
    </div>
  );
}

export function CurrentPlanCard({ planActual, loading = false, error, onRetry, restricted = false }) {
  const plan = planActual?.plan;

  return (
    <Card>
      <CardHeader title="Plan actual" description="Limites comerciales aplicados a esta organizacion." />
      {loading ? <LoadingPlan /> : null}
      {!loading && error ? <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} /> : null}
      {!loading && restricted ? (
        <ErrorState
          title="Plan actual restringido"
          message="El backend actual restringe esta consulta a owner, admin o super_admin."
        />
      ) : null}
      {!loading && !error && !restricted && plan ? (
        <div className="space-y-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
                <CreditCard className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-semibold text-slate-950">{plan.nombre}</h2>
                  <PlanBadge plan={plan} current />
                </div>
                <p className="mt-1 text-sm text-slate-500">{plan.descripcion || `Codigo ${plan.codigo}`}</p>
              </div>
            </div>
            <p className="text-sm font-semibold text-slate-950">{formatCurrency(plan.precio_mensual, "USD")} / mes</p>
          </div>
          <PlanLimitsCard plan={plan} />
          <PlanFeatureList plan={plan} />
        </div>
      ) : null}
    </Card>
  );
}
