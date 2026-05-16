import { RotateCcw, Send } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatDateTime } from "../../../shared/utils/formatters";
import { DeliveryStatusBadge } from "./DeliveryStatusBadge";

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
      ))}
    </div>
  );
}

function canRetryDelivery(delivery, canRetry) {
  return canRetry && ["fallido", "pendiente"].includes(delivery.status);
}

export function WebhookDeliveriesTable({
  deliveries = [],
  loading = false,
  error,
  onRetryQuery,
  onRetryDelivery,
  retryingId,
  canRetry = false,
}) {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetryQuery} />;
  }

  if (!deliveries.length) {
    return (
      <EmptyState
        icon={Send}
        title="Todavia no hay deliveries"
        description="Cuando se disparen eventos para webhooks, los intentos apareceran en esta tabla."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[1100px] w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-slate-400">
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Evento</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Status</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">HTTP</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Intentos</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Creacion</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Ultimo intento</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Error</th>
            <th className="border-b border-slate-200 px-3 py-3 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {deliveries.map((delivery) => (
            <tr key={delivery.id} className="align-middle text-slate-700">
              <td className="border-b border-slate-100 px-3 py-3 font-mono text-xs">{delivery.evento}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <DeliveryStatusBadge status={delivery.status} />
              </td>
              <td className="border-b border-slate-100 px-3 py-3">{delivery.status_code ?? "-"}</td>
              <td className="border-b border-slate-100 px-3 py-3">{delivery.intentos}</td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(delivery.fecha_creacion)}</td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(delivery.fecha_ultimo_intento)}</td>
              <td className="max-w-[260px] truncate border-b border-slate-100 px-3 py-3" title={delivery.error || ""}>
                {delivery.error || "-"}
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex justify-end">
                  {canRetryDelivery(delivery, canRetry) ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={RotateCcw}
                      loading={retryingId === delivery.id}
                      onClick={() => onRetryDelivery(delivery)}
                    >
                      Reenviar
                    </Button>
                  ) : (
                    <span className="text-sm text-slate-400">-</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
