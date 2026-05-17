import { Link } from "react-router-dom";
import { ArrowRight, ReceiptText } from "lucide-react";

import { getApiErrorMessage } from "../../../../shared/api/apiError";
import { Card, CardHeader } from "../../../../shared/components/ui/Card";
import { EmptyState } from "../../../../shared/components/ui/EmptyState";
import { ROUTES } from "../../../../shared/utils/constants";
import { formatCurrency, formatDateTime } from "../../../../shared/utils/formatters";
import { MovementStatusBadge } from "../../../movimientos/components/MovementStatusBadge";
import { MovementTypeBadge } from "../../../movimientos/components/MovementTypeBadge";

export function ClientRecentMovements({ movements = [], loading, error, onRetry }) {
  return (
    <Card className="xl:col-span-2">
      <CardHeader
        title="Movimientos recientes"
        description="Ultimas operaciones asociadas a tus wallets."
        action={
          <Link className="inline-flex items-center gap-2 text-sm font-medium text-brand-primary hover:underline" to={ROUTES.movimientos}>
            Ver todos
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        }
      />
      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-16 animate-pulse rounded-md bg-slate-100" />
          ))}
        </div>
      ) : null}
      {!loading && error ? (
        <div className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
          {getApiErrorMessage(error)}
          {onRetry ? (
            <button className="ml-2 text-rose-900 underline" type="button" onClick={onRetry}>
              Reintentar
            </button>
          ) : null}
        </div>
      ) : null}
      {!loading && !error && movements.length === 0 ? (
        <EmptyState title="Todavia no hay movimientos" description="Tus pagos y operaciones van a aparecer aca." icon={ReceiptText} />
      ) : null}
      {!loading && !error && movements.length > 0 ? (
        <div className="divide-y divide-slate-100">
          {movements.map((movement) => (
            <div key={movement.id} className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <MovementTypeBadge movement={movement} />
                  <MovementStatusBadge estado={movement.estado} />
                </div>
                <p className="mt-1 truncate text-sm text-slate-500">{movement.descripcion || movement.referencia_externa || "Sin descripcion"}</p>
                <p className="mt-1 text-xs text-slate-400">{formatDateTime(movement.fecha)}</p>
              </div>
              <div className="text-left sm:text-right">
                <p className="text-sm font-semibold text-slate-950">{formatCurrency(movement.monto, movement.moneda)}</p>
                <p className="mt-1 text-xs text-slate-400">{movement.moneda}</p>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </Card>
  );
}
