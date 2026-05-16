import { CheckCircle2, XCircle } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { Badge } from "../../../shared/components/ui/Badge";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { formatCurrency, formatLimit } from "../../../shared/utils/formatters";

function FeatureFlag({ enabled, label }) {
  const Icon = enabled ? CheckCircle2 : XCircle;
  return (
    <Badge tone={enabled ? "success" : "neutral"} className="gap-1.5">
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </Badge>
  );
}

function LoadingRows() {
  return (
    <div className="space-y-3">
      <div className="h-7 w-32 animate-pulse rounded-md bg-slate-100" />
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="h-12 animate-pulse rounded-md bg-slate-100" />
        <div className="h-12 animate-pulse rounded-md bg-slate-100" />
        <div className="h-12 animate-pulse rounded-md bg-slate-100" />
      </div>
    </div>
  );
}

export function PlanSummaryCard({ planActual, loading, error }) {
  const plan = planActual?.plan;

  return (
    <Card>
      <CardHeader title="Plan actual" description="Limites comerciales aplicados a esta organizacion." />
      {loading ? <LoadingRows /> : null}
      {!loading && error ? <p className="text-sm text-rose-700">{getApiErrorMessage(error)}</p> : null}
      {!loading && !error && plan ? (
        <div className="space-y-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-2xl font-semibold text-slate-950">{plan.nombre}</p>
              <p className="mt-1 text-sm text-slate-500">{plan.descripcion || `Codigo ${plan.codigo}`}</p>
            </div>
            <p className="text-sm font-semibold text-slate-950">{formatCurrency(plan.precio_mensual, "USD")} / mes</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <LimitItem label="Usuarios" value={formatLimit(plan.limite_usuarios)} />
            <LimitItem label="Wallets" value={formatLimit(plan.limite_wallets)} />
            <LimitItem label="Movimientos mes" value={formatLimit(plan.limite_movimientos_mes)} />
          </div>
          <div className="flex flex-wrap gap-2">
            <FeatureFlag enabled={plan.permite_webhooks} label="Webhooks" />
            <FeatureFlag enabled={plan.permite_white_label} label="White-label" />
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function LimitItem({ label, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
      <p className="text-xs font-medium uppercase text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
