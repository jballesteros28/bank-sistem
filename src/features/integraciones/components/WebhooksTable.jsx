import { Power, RadioTower, Trash2 } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Badge } from "../../../shared/components/ui/Badge";
import { Button } from "../../../shared/components/ui/Button";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatDateTime } from "../../../shared/utils/formatters";

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
      ))}
    </div>
  );
}

function ActiveBadge({ active }) {
  return <Badge tone={active ? "success" : "neutral"}>{active ? "Activo" : "Inactivo"}</Badge>;
}

export function WebhooksTable({
  webhooks = [],
  loading = false,
  error,
  onRetry,
  onToggle,
  onDelete,
  updatingId,
  deletingId,
  canManage = false,
}) {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!webhooks.length) {
    return (
      <EmptyState
        icon={RadioTower}
        title="Todavia no hay webhooks"
        description="Crea un endpoint para recibir eventos de wallets, movimientos y notificaciones."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[1040px] w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-slate-400">
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Nombre</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">URL</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Eventos</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Estado</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Creacion</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Actualizacion</th>
            <th className="border-b border-slate-200 px-3 py-3 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {webhooks.map((webhook) => (
            <tr key={webhook.id} className="align-middle text-slate-700">
              <td className="border-b border-slate-100 px-3 py-3 font-medium text-slate-950">{webhook.nombre}</td>
              <td className="max-w-[280px] truncate border-b border-slate-100 px-3 py-3" title={webhook.url}>
                {webhook.url}
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex max-w-[320px] flex-wrap gap-1.5">
                  {(webhook.eventos || []).map((event) => (
                    <Badge key={event} tone="info" className="font-mono">
                      {event}
                    </Badge>
                  ))}
                </div>
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <ActiveBadge active={webhook.activo} />
              </td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(webhook.fecha_creacion)}</td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(webhook.fecha_actualizacion)}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex justify-end gap-2">
                  {canManage ? (
                    <>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={Power}
                        loading={updatingId === webhook.id}
                        onClick={() => onToggle(webhook)}
                      >
                        {webhook.activo ? "Pausar" : "Activar"}
                      </Button>
                      {webhook.activo ? (
                        <Button
                          variant="danger"
                          size="sm"
                          icon={Trash2}
                          loading={deletingId === webhook.id}
                          onClick={() => onDelete(webhook)}
                        >
                          Eliminar
                        </Button>
                      ) : null}
                    </>
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
