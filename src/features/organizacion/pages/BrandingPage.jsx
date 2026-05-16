import { useQuery } from "@tanstack/react-query";

import { useBranding } from "../api";
import { BrandingForm } from "../components/BrandingForm";
import { getPlanActual, planQueryKeys } from "../../planes/api";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canEditBranding, canViewBranding, canViewCurrentPlan } from "../../../shared/utils/roles";

function BrandingLoading() {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-6">
        {[0, 1, 2].map((item) => (
          <Card key={item}>
            <div className="h-6 w-40 animate-pulse rounded bg-slate-100" />
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="h-11 animate-pulse rounded bg-slate-100" />
              <div className="h-11 animate-pulse rounded bg-slate-100" />
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <div className="h-64 animate-pulse rounded bg-slate-100" />
      </Card>
    </div>
  );
}

export function BrandingPage() {
  const { user } = useAuth();
  const canView = canViewBranding(user);
  const canEdit = canEditBranding(user);
  const canLoadCurrentPlan = canViewCurrentPlan(user);
  const brandingQuery = useBranding({ enabled: canView });
  const branding = brandingQuery.data;
  const planActualQuery = useQuery({
    queryKey: planQueryKeys.current(user?.organizacion_id),
    queryFn: getPlanActual,
    enabled: canLoadCurrentPlan,
    retry: false,
  });
  const plan = planActualQuery.data?.plan;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Branding de organizacion</h1>
        <p className="mt-1 text-sm text-slate-500">Administra marca, colores, dominio y configuracion regional.</p>
      </div>
      {!canView ? (
        <Card>
          <CardHeader title="Sin permisos" description="La gestion de branding esta reservada a roles de organizacion." />
          <EmptyState title="No tenes permisos para ver branding." description="Solicita acceso a un owner o admin de la organizacion." />
        </Card>
      ) : null}
      {canView && brandingQuery.isLoading ? <BrandingLoading /> : null}
      {canView && brandingQuery.isError ? (
        <ErrorState message="No pudimos obtener el branding actual." onRetry={() => brandingQuery.refetch()} />
      ) : null}
      {canView && planActualQuery.isError ? (
        <ErrorState
          title="Plan no disponible"
          message="No pudimos consultar el plan actual. El formulario sigue disponible, pero las opciones white-label avanzadas quedan bloqueadas."
          onRetry={() => planActualQuery.refetch()}
        />
      ) : null}
      {canView && !brandingQuery.isLoading && !brandingQuery.isError && branding ? (
        <BrandingForm branding={branding} plan={plan} canEdit={canEdit} />
      ) : null}
    </div>
  );
}
