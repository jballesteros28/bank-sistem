import { useQuery } from "@tanstack/react-query";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { getPlanActual, planQueryKeys } from "../../planes/api";
import { ApiKeysPanel } from "../components/ApiKeysPanel";
import { IntegrationsTabs } from "../components/IntegrationsTabs";
import { WebhookDeliveriesPanel } from "../components/WebhookDeliveriesPanel";
import { WebhooksPanel } from "../components/WebhooksPanel";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canManageApiKeys, canManageWebhooks, canViewWebhookDeliveries, isClient } from "../../../shared/utils/roles";

function SummaryHeader({ planActual, planLoading, planError }) {
  const plan = planActual?.plan;

  return (
    <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
      <Card className="bg-slate-50">
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-white text-brand-primary ring-1 ring-slate-200">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-950">Integraciones externas</h2>
            <p className="mt-1 text-sm text-slate-600">
              Gestiona credenciales, endpoints webhook y deliveries sin exponer secretos completos en listados.
            </p>
            <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-900">
              Las API Keys solo se muestran una vez al crearlas.
            </p>
          </div>
        </div>
      </Card>
      <Card>
        <p className="text-sm font-medium text-slate-500">Plan actual</p>
        {planLoading ? <div className="mt-3 h-8 w-40 animate-pulse rounded bg-slate-100" /> : null}
        {!planLoading && plan ? (
          <>
            <p className="mt-2 text-2xl font-semibold text-slate-950">{plan.nombre}</p>
            <p className="mt-1 text-sm text-slate-500">
              Webhooks {plan.permite_webhooks ? "habilitados" : "no incluidos"} para esta organizacion.
            </p>
          </>
        ) : null}
        {!planLoading && !plan && planError ? (
          <p className="mt-2 text-sm text-slate-500">No pudimos confirmar el plan actual para tu rol.</p>
        ) : null}
      </Card>
    </div>
  );
}

export function IntegracionesPage() {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState("apiKeys");
  const canAccess = Boolean(user) && !isClient(user);
  const canManageKeys = canManageApiKeys(user);
  const canManageHooksByRole = canManageWebhooks(user);
  const canViewDeliveries = canViewWebhookDeliveries(user);

  const planActualQuery = useQuery({
    queryKey: planQueryKeys.current(user?.organizacion_id),
    queryFn: getPlanActual,
    enabled: Boolean(token) && canAccess,
    retry: false,
  });

  const planAllowsWebhooks = Boolean(planActualQuery.data?.plan?.permite_webhooks);
  const canRetryDeliveries = canManageWebhooks(user, planAllowsWebhooks);

  const renderActivePanel = () => {
    if (activeTab === "webhooks") {
      return (
        <WebhooksPanel
          user={user}
          canView={canAccess}
          canManageByRole={canManageHooksByRole}
          planAllowsWebhooks={planAllowsWebhooks}
          planLoading={planActualQuery.isLoading}
          planError={planActualQuery.error}
        />
      );
    }

    if (activeTab === "deliveries") {
      return <WebhookDeliveriesPanel user={user} canView={canViewDeliveries} canRetry={canRetryDeliveries} />;
    }

    return <ApiKeysPanel user={user} canManage={canManageKeys} canView={canAccess} />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">API Keys y Webhooks</h1>
        <p className="mt-1 text-sm text-slate-500">Administra acceso externo, eventos, deliveries y reintentos manuales.</p>
      </div>

      {!canAccess ? (
        <Card>
          <CardHeader title="Sin permisos" description="La gestion de integraciones esta limitada por rol." />
          <EmptyState
            icon={LockKeyhole}
            title="No tenes permisos para acceder a integraciones."
            description="Tu rol actual no puede gestionar API Keys, webhooks ni deliveries."
          />
        </Card>
      ) : (
        <>
          <SummaryHeader planActual={planActualQuery.data} planLoading={planActualQuery.isLoading} planError={planActualQuery.error} />
          <IntegrationsTabs activeTab={activeTab} onChange={setActiveTab} />
          {renderActivePanel()}
        </>
      )}
    </div>
  );
}
