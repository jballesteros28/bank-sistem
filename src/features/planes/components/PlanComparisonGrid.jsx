import { ArrowRight } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { formatCurrency, formatLimit } from "../../../shared/utils/formatters";
import { PlanBadge } from "./PlanBadge";
import { PlanFeatureList } from "./PlanFeatureList";

export function PlanComparisonGrid({ plans = [], currentPlanCode }) {
  if (!plans.length) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {plans.map((plan) => {
        const current = plan.codigo === currentPlanCode;
        return (
          <article
            key={plan.id}
            className={[
              "rounded-lg border bg-white p-5 shadow-sm",
              current ? "border-brand-primary/40 ring-1 ring-brand-primary/10" : "border-slate-200",
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-950">{plan.nombre}</h3>
                <p className="mt-1 text-sm text-slate-500">{plan.descripcion || plan.codigo}</p>
              </div>
              <PlanBadge plan={plan} current={current} />
            </div>
            <p className="mt-5 text-2xl font-semibold text-slate-950">{formatCurrency(plan.precio_mensual, "USD")}</p>
            <p className="mt-1 text-sm text-slate-500">por mes</p>
            <dl className="mt-5 space-y-2 text-sm">
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Usuarios</dt>
                <dd className="font-medium text-slate-900">{formatLimit(plan.limite_usuarios)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Wallets</dt>
                <dd className="font-medium text-slate-900">{formatLimit(plan.limite_wallets)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Movimientos</dt>
                <dd className="font-medium text-slate-900">{formatLimit(plan.limite_movimientos_mes)}</dd>
              </div>
            </dl>
            <div className="mt-5">
              <PlanFeatureList plan={plan} />
            </div>
            <Button className="mt-5 w-full" variant={current ? "secondary" : "primary"} icon={ArrowRight} disabled>
              {current ? "Plan actual" : "Proximamente"}
            </Button>
          </article>
        );
      })}
    </div>
  );
}
