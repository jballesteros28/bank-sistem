import { useQuery } from "@tanstack/react-query";

import { CurrentPlanCard } from "../components/CurrentPlanCard";
import { PlanComparisonGrid } from "../components/PlanComparisonGrid";
import { getPlanActual, listPlanes, planQueryKeys } from "../api";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canViewCurrentPlan, canViewPlans } from "../../../shared/utils/roles";

function PlanGridLoading() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {[0, 1, 2, 3].map((item) => (
        <div key={item} className="h-80 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
      ))}
    </div>
  );
}

export function PlanesPage() {
  const { token, user } = useAuth();
  const canView = canViewPlans(user);
  const canLoadCurrentPlan = canViewCurrentPlan(user);
  const planActualQuery = useQuery({
    queryKey: planQueryKeys.current(user?.organizacion_id),
    queryFn: getPlanActual,
    enabled: Boolean(token) && canLoadCurrentPlan,
    retry: false,
  });
  const plansQuery = useQuery({
    queryKey: planQueryKeys.list,
    queryFn: listPlanes,
    enabled: Boolean(token) && canView,
    retry: false,
  });
  const plans = plansQuery.data || [];
  const currentPlan = planActualQuery.data?.plan;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Plan actual y limites</h1>
        <p className="mt-1 text-sm text-slate-500">Consulta capacidades, limites mensuales y habilitaciones SaaS.</p>
      </div>
      {!canView ? (
        <Card>
          <CardHeader title="Sin permisos" description="La consulta de planes esta limitada por rol." />
          <EmptyState title="No tenes permisos para ver planes." description="Tu rol actual no puede consultar limites comerciales." />
        </Card>
      ) : null}
      {canView ? (
        <>
          <CurrentPlanCard
            planActual={planActualQuery.data}
            loading={planActualQuery.isLoading}
            error={planActualQuery.error}
            onRetry={() => planActualQuery.refetch()}
            restricted={!canLoadCurrentPlan}
          />
          <Card>
            <CardHeader title="Planes disponibles" description="Comparacion comercial de capacidades SaaS." />
            {plansQuery.isLoading ? <PlanGridLoading /> : null}
            {!plansQuery.isLoading && plansQuery.isError ? (
              <ErrorState message="No pudimos cargar los planes disponibles." onRetry={() => plansQuery.refetch()} />
            ) : null}
            {!plansQuery.isLoading && !plansQuery.isError && !plans.length ? (
              <EmptyState title="Sin planes disponibles" description="El catalogo de planes todavia no esta disponible." />
            ) : null}
            {!plansQuery.isLoading && !plansQuery.isError && plans.length ? (
              <PlanComparisonGrid plans={plans} currentPlanCode={currentPlan?.codigo} />
            ) : null}
          </Card>
        </>
      ) : null}
    </div>
  );
}
