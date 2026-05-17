import { Bell, CreditCard, ReceiptText, WalletCards } from "lucide-react";

import { DashboardHeader } from "../components/DashboardHeader";
import { MetricCard } from "../components/MetricCard";
import { NotificationsSummaryCard } from "../components/NotificationsSummaryCard";
import { OrganizationWalletCard } from "../components/OrganizationWalletCard";
import { PlanSummaryCard } from "../components/PlanSummaryCard";
import { QuickActions } from "../components/QuickActions";
import { RecentMovementsCard } from "../components/RecentMovementsCard";
import { ClientDashboard } from "../components/client/ClientDashboard";
import { useDashboardData } from "../hooks/useDashboardData";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { formatCurrency, formatLimit, formatNumber } from "../../../shared/utils/formatters";
import { isClient } from "../../../shared/utils/roles";

export function DashboardPage() {
  const { user } = useAuth();
  const isClientDashboard = isClient(user);
  const dashboard = useDashboardData({ enabled: !isClientDashboard });

  const branding = dashboard.brandingQuery.data;
  const planActual = dashboard.planQuery.data;
  const plan = planActual?.plan;
  const walletPrincipal = dashboard.walletPrincipalQuery.data;
  const organizationWallets = dashboard.organizationWalletsQuery.data || [];
  const recentMovements = dashboard.recentMovementsQuery.data || [];
  const unreadNotifications = dashboard.unreadNotificationsQuery.data || 0;
  const walletLimitDescription = dashboard.planQuery.isLoading
    ? "Limite del plan: cargando"
    : `Limite del plan: ${plan ? formatLimit(plan.limite_wallets) : "no disponible"}`;
  const movementsLimitDescription = dashboard.planQuery.isLoading
    ? "Limite mensual: cargando"
    : `Limite mensual: ${plan ? formatLimit(plan.limite_movimientos_mes) : "no disponible"}`;

  if (isClientDashboard) {
    return <ClientDashboard />;
  }

  return (
    <div className="space-y-6">
      <DashboardHeader user={user} branding={branding} />
      {!dashboard.hasOrganization ? (
        <ErrorState
          title="Usuario sin organizacion"
          message="Este dashboard necesita una organizacion asociada para cargar plan, wallets, movimientos y notificaciones."
        />
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Wallets organizacion"
          value={formatNumber(organizationWallets.length)}
          description={walletLimitDescription}
          icon={CreditCard}
          loading={dashboard.organizationWalletsQuery.isLoading}
          error={dashboard.organizationWalletsQuery.isError}
        />
        <MetricCard
          title="Saldo principal"
          value={walletPrincipal ? formatCurrency(walletPrincipal.saldo, walletPrincipal.moneda) : "-"}
          description={walletPrincipal?.alias || "Wallet empresa"}
          icon={WalletCards}
          loading={dashboard.walletPrincipalQuery.isLoading}
          error={dashboard.walletPrincipalQuery.isError}
        />
        <MetricCard
          title="Movimientos recientes"
          value={formatNumber(recentMovements.length)}
          description={movementsLimitDescription}
          icon={ReceiptText}
          loading={dashboard.recentMovementsQuery.isLoading}
          error={dashboard.recentMovementsQuery.isError}
        />
        <MetricCard
          title="No leidas"
          value={formatNumber(unreadNotifications)}
          description="Notificaciones pendientes"
          icon={Bell}
          loading={dashboard.unreadNotificationsQuery.isLoading}
          error={dashboard.unreadNotificationsQuery.isError}
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <PlanSummaryCard planActual={planActual} loading={dashboard.planQuery.isLoading} error={dashboard.planQuery.error} />
        <OrganizationWalletCard
          wallet={walletPrincipal}
          loading={dashboard.walletPrincipalQuery.isLoading}
          error={dashboard.walletPrincipalQuery.error}
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <RecentMovementsCard
          movements={recentMovements}
          loading={dashboard.recentMovementsQuery.isLoading}
          error={dashboard.recentMovementsQuery.error}
        />
        <div className="space-y-6">
          <NotificationsSummaryCard
            count={unreadNotifications}
            loading={dashboard.unreadNotificationsQuery.isLoading}
            error={dashboard.unreadNotificationsQuery.error}
          />
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
