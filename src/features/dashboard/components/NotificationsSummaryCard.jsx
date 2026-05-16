import { Link } from "react-router-dom";
import { ArrowRight, Bell } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { ROUTES } from "../../../shared/utils/constants";
import { formatNumber } from "../../../shared/utils/formatters";

export function NotificationsSummaryCard({ count = 0, loading, error }) {
  const hasUnread = Number(count || 0) > 0;

  return (
    <Card>
      <CardHeader title="Notificaciones" description="Alertas internas pendientes de lectura." />
      {loading ? <div className="h-24 animate-pulse rounded-md bg-slate-100" /> : null}
      {!loading && error ? <p className="text-sm text-rose-700">{getApiErrorMessage(error)}</p> : null}
      {!loading && !error ? (
        <div className="space-y-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-3xl font-semibold text-slate-950">{formatNumber(count)}</p>
              <p className="mt-1 text-sm text-slate-500">{hasUnread ? "Pendientes por revisar" : "Todo al dia"}</p>
            </div>
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
              <Bell className="h-5 w-5" aria-hidden="true" />
            </div>
          </div>
          <Link className="inline-flex items-center gap-2 text-sm font-medium text-brand-primary hover:underline" to={ROUTES.notificaciones}>
            Ver notificaciones
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      ) : null}
    </Card>
  );
}
