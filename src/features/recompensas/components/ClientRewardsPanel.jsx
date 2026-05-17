import { useQuery } from "@tanstack/react-query";
import { Gift } from "lucide-react";
import { useMemo } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatCurrency, formatDateTime, formatNumber } from "../../../shared/utils/formatters";
import { getMyRewardApplications, rewardQueryKeys } from "../api";
import { RewardApplicationsTable } from "./RewardApplicationsTable";

const emptyArray = [];

function formatRewardValue(value, currency) {
  if (currency === "PUNTOS") {
    return `${formatNumber(value)} PUNTOS`;
  }
  return formatCurrency(value, currency);
}

function TotalsSummary({ totals }) {
  const entries = Object.entries(totals);
  if (!entries.length) {
    return null;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {entries.map(([currency, amount]) => (
        <div key={currency} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-medium uppercase tracking-normal text-slate-500">{currency}</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{formatRewardValue(amount, currency)}</p>
        </div>
      ))}
    </div>
  );
}

function MobileRewardList({ rewards }) {
  if (!rewards.length) {
    return null;
  }

  return (
    <div className="grid gap-3 md:hidden">
      {rewards.map((reward) => (
        <article key={reward.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">{formatRewardValue(reward.monto_recompensa, reward.moneda_recompensa)}</p>
              <p className="mt-1 text-xs text-slate-500">{formatDateTime(reward.fecha_creacion)}</p>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">{reward.moneda_recompensa}</span>
          </div>
          {reward.referencia_externa ? <p className="mt-3 text-sm text-slate-600">{reward.referencia_externa}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function ClientRewardsPanel({ user }) {
  const organizationId = user?.organizacion_id || "current";

  const rewardsQuery = useQuery({
    queryKey: rewardQueryKeys.myRewardApplications(organizationId, { skip: 0, limit: 100 }),
    queryFn: () => getMyRewardApplications({ skip: 0, limit: 100 }),
    retry: false,
  });

  const rewards = rewardsQuery.data || emptyArray;
  const totals = useMemo(
    () =>
      rewards.reduce((acc, reward) => {
        const currency = reward.moneda_recompensa || "ARS";
        const amount = Number(reward.monto_recompensa);
        acc[currency] = (acc[currency] || 0) + (Number.isFinite(amount) ? amount : 0);
        return acc;
      }, {}),
    [rewards],
  );

  return (
    <Card>
      <CardHeader title="Mis recompensas" description="Cashback, puntos y credito interno recibidos en tus wallets." />

      {rewardsQuery.isLoading ? (
        <div className="space-y-3">
          <div className="h-20 animate-pulse rounded-lg bg-slate-100" />
          <div className="h-36 animate-pulse rounded-lg bg-slate-100" />
        </div>
      ) : rewardsQuery.error ? (
        <ErrorState title="No se pudieron cargar tus recompensas" message={getApiErrorMessage(rewardsQuery.error)} onRetry={() => rewardsQuery.refetch()} />
      ) : !rewards.length ? (
        <EmptyState icon={Gift} title="Todavia no recibiste recompensas" description="Cuando una compra genere cashback, puntos o credito, la vas a ver aca." />
      ) : (
        <div className="space-y-5">
          <TotalsSummary totals={totals} />
          <MobileRewardList rewards={rewards} />
          <div className="hidden md:block">
            <RewardApplicationsTable applications={rewards} showUser={false} />
          </div>
        </div>
      )}
    </Card>
  );
}
