import { Link } from "react-router-dom";
import { ArrowRight, ReceiptText } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { Badge } from "../../../shared/components/ui/Badge";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { ROUTES } from "../../../shared/utils/constants";
import { formatCurrency, formatDateTime } from "../../../shared/utils/formatters";

function humanize(value) {
  return String(value || "-").replace(/_/g, " ");
}

function movementTone(status) {
  if (status === "aprobada") {
    return "success";
  }
  if (status === "rechazada" || status === "cancelada") {
    return "danger";
  }
  if (status === "pendiente") {
    return "warning";
  }
  return "neutral";
}

export function RecentMovementsCard({ movements = [], loading, error }) {
  return (
    <Card className="xl:col-span-2">
      <CardHeader
        title="Movimientos recientes"
        description="Ultimas operaciones visibles para tu organizacion."
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
      {!loading && error ? <p className="text-sm text-rose-700">{getApiErrorMessage(error)}</p> : null}
      {!loading && !error && movements.length === 0 ? (
        <EmptyState title="Todavia no hay movimientos" description="Las operaciones aprobadas apareceran en este resumen." icon={ReceiptText} />
      ) : null}
      {!loading && !error && movements.length > 0 ? (
        <div className="divide-y divide-slate-100">
          {movements.map((movement) => (
            <div key={movement.id} className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold capitalize text-slate-950">{humanize(movement.tipo)}</p>
                  <Badge tone={movementTone(movement.estado)}>{humanize(movement.estado)}</Badge>
                </div>
                <p className="mt-1 truncate text-sm text-slate-500">{movement.descripcion || movement.referencia_externa || "Sin descripcion"}</p>
                <p className="mt-1 text-xs text-slate-400">{formatDateTime(movement.fecha)}</p>
              </div>
              <p className="text-sm font-semibold text-slate-950">{formatCurrency(movement.monto, movement.moneda)}</p>
            </div>
          ))}
        </div>
      ) : null}
    </Card>
  );
}
