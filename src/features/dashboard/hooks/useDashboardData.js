import { useQuery } from "@tanstack/react-query";

import { getMovimientos } from "../../movimientos/api";
import { getUnreadNotificationsCount } from "../../notificaciones/api";
import { useBranding } from "../../organizacion/api";
import { getPlanActual } from "../../planes/api";
import { getWalletPrincipalOrganizacion, getWalletsOrganizacion } from "../../wallets/api";
import { useAuth } from "../../../shared/hooks/useAuth";

const DASHBOARD_STALE_TIME = 60_000;

export function useDashboardData({ enabled = true } = {}) {
  const { token, user } = useAuth();
  const hasToken = Boolean(token);
  const hasOrganization = Boolean(user?.organizacion_id);
  const canLoadOrganizationData = enabled && hasToken && hasOrganization;

  const brandingQuery = useBranding({ enabled: canLoadOrganizationData });

  const planQuery = useQuery({
    queryKey: ["dashboard", "plan-actual", user?.organizacion_id],
    queryFn: getPlanActual,
    enabled: canLoadOrganizationData,
    retry: false,
    staleTime: DASHBOARD_STALE_TIME,
  });

  const walletPrincipalQuery = useQuery({
    queryKey: ["dashboard", "wallet-principal-organizacion", user?.organizacion_id],
    queryFn: () => getWalletPrincipalOrganizacion(),
    enabled: canLoadOrganizationData,
    retry: false,
    staleTime: DASHBOARD_STALE_TIME,
  });

  const organizationWalletsQuery = useQuery({
    queryKey: ["dashboard", "wallets-organizacion", user?.organizacion_id],
    queryFn: () => getWalletsOrganizacion(),
    enabled: canLoadOrganizationData,
    retry: false,
    staleTime: DASHBOARD_STALE_TIME,
  });

  const recentMovementsQuery = useQuery({
    queryKey: ["dashboard", "movimientos-recientes", user?.organizacion_id],
    queryFn: () => getMovimientos({ skip: 0, limit: 5 }),
    enabled: canLoadOrganizationData,
    retry: false,
    staleTime: DASHBOARD_STALE_TIME,
  });

  const unreadNotificationsQuery = useQuery({
    queryKey: ["dashboard", "notificaciones-no-leidas", user?.organizacion_id],
    queryFn: getUnreadNotificationsCount,
    enabled: canLoadOrganizationData,
    retry: false,
    staleTime: DASHBOARD_STALE_TIME,
  });

  const queries = [
    brandingQuery,
    planQuery,
    walletPrincipalQuery,
    organizationWalletsQuery,
    recentMovementsQuery,
    unreadNotificationsQuery,
  ];

  return {
    brandingQuery,
    planQuery,
    walletPrincipalQuery,
    organizationWalletsQuery,
    recentMovementsQuery,
    unreadNotificationsQuery,
    isInitialLoading: queries.filter((query) => query.isLoading).length >= 4,
    hasOrganization,
  };
}
