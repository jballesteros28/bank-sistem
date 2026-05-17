import { AlertTriangle, CheckCircle2, Gift, ShoppingBag } from "lucide-react";

import { formatNumber } from "../../../shared/utils/formatters";

function SummaryCard({ title, value, description, icon: Icon, loading = false }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          {loading ? (
            <div className="mt-3 h-7 w-24 animate-pulse rounded bg-slate-100" />
          ) : (
            <p className="mt-2 truncate text-2xl font-semibold text-slate-950">{formatNumber(value)}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

export function EcommerceSummary({ orders = [], loading = false }) {
  const total = orders.length;
  const processed = orders.filter((order) => order.procesado && !order.error_procesamiento).length;
  const failed = orders.filter((order) => Boolean(order.error_procesamiento)).length;
  const rewarded = orders.filter((order) => Boolean(order.recompensa_aplicada_id)).length;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <SummaryCard title="Ordenes recibidas" value={total} description="Eventos ecommerce cargados" icon={ShoppingBag} loading={loading} />
      <SummaryCard title="Procesadas OK" value={processed} description="Sin error de procesamiento" icon={CheckCircle2} loading={loading} />
      <SummaryCard title="Con error" value={failed} description="Requieren revision operativa" icon={AlertTriangle} loading={loading} />
      <SummaryCard title="Recompensas aplicadas" value={rewarded} description="Cashback o store credit" icon={Gift} loading={loading} />
    </div>
  );
}
