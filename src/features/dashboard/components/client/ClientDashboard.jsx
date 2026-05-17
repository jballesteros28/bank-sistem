import { useQuery } from "@tanstack/react-query";
import { useMemo, useRef } from "react";

import { getMovimientos } from "../../../movimientos/api";
import { getUnreadNotificationsCount, notificationQueryKeys } from "../../../notificaciones/api";
import { useBranding } from "../../../organizacion/api";
import { getWalletsUsuario, walletQueryKeys } from "../../../wallets/api";
import { useAuth } from "../../../../shared/hooks/useAuth";
import { formatCurrency } from "../../../../shared/utils/formatters";
import { ClientQuickActions } from "./ClientQuickActions";
import { ClientRecentMovements } from "./ClientRecentMovements";
import { ClientWalletCard } from "./ClientWalletCard";
import { PayOrganizationCard } from "./PayOrganizationCard";

const emptyArray = [];

function pickMainWallet(wallets) {
  return wallets.find((wallet) => wallet.es_principal) || wallets[0] || null;
}

export function ClientDashboard() {
  const { token, user } = useAuth();
  const paymentRef = useRef(null);
  const hasToken = Boolean(token);
  const organizationId = user?.organizacion_id || "current";

  const brandingQuery = useBranding({ enabled: hasToken });

  const walletsQuery = useQuery({
    queryKey: walletQueryKeys.user(organizationId),
    queryFn: () => getWalletsUsuario(),
    enabled: hasToken,
    retry: false,
  });

  const movementsQuery = useQuery({
    queryKey: ["dashboard", "cliente", "movimientos-recientes", organizationId],
    queryFn: () => getMovimientos({ skip: 0, limit: 5 }),
    enabled: hasToken,
    retry: false,
    staleTime: 60_000,
  });

  const unreadNotificationsQuery = useQuery({
    queryKey: notificationQueryKeys.unreadCount,
    queryFn: getUnreadNotificationsCount,
    enabled: hasToken,
    retry: false,
    staleTime: 60_000,
  });

  const wallets = walletsQuery.data || emptyArray;
  const movements = movementsQuery.data || emptyArray;
  const mainWallet = useMemo(() => pickMainWallet(wallets), [wallets]);
  const organizationName = brandingQuery.data?.nombre_comercial || brandingQuery.data?.nombre || "tu organizacion";

  const scrollToPayment = () => {
    paymentRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium text-brand-primary">{organizationName}</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal text-slate-950">Hola, {user?.nombre || "usuario"}</h1>
            <p className="mt-1 text-sm text-slate-500">Tu wallet, pagos y notificaciones en un solo lugar.</p>
          </div>
          <div className="rounded-md bg-slate-50 px-4 py-3">
            <p className="text-xs font-medium uppercase text-slate-400">Saldo principal</p>
            <p className="mt-1 text-2xl font-semibold text-slate-950">
              {mainWallet ? formatCurrency(mainWallet.saldo, mainWallet.moneda) : "-"}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <ClientWalletCard
            wallet={mainWallet}
            loading={walletsQuery.isLoading}
            error={walletsQuery.error}
            onRetry={() => walletsQuery.refetch()}
          />
          <div ref={paymentRef}>
            <PayOrganizationCard wallets={wallets} loading={walletsQuery.isLoading} />
          </div>
        </div>
        <ClientQuickActions
          unreadCount={unreadNotificationsQuery.data || 0}
          unreadLoading={unreadNotificationsQuery.isLoading}
          onPay={scrollToPayment}
        />
      </div>

      <ClientRecentMovements
        movements={movements}
        loading={movementsQuery.isLoading}
        error={movementsQuery.error}
        onRetry={() => movementsQuery.refetch()}
      />
    </div>
  );
}
