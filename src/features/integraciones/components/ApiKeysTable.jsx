import { Ban, KeyRound } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Badge } from "../../../shared/components/ui/Badge";
import { Button } from "../../../shared/components/ui/Button";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatDateTime } from "../../../shared/utils/formatters";

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
      ))}
    </div>
  );
}

function ActiveBadge({ active }) {
  return <Badge tone={active ? "success" : "neutral"}>{active ? "Activa" : "Revocada"}</Badge>;
}

export function ApiKeysTable({ apiKeys = [], loading = false, error, onRetry, onRevoke, revokingId, canManage = false }) {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!apiKeys.length) {
    return (
      <EmptyState
        icon={KeyRound}
        title="Todavia no hay API Keys"
        description="Crea una key para conectar sistemas externos con scopes limitados."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[940px] w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-slate-400">
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Nombre</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Prefix</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Scopes</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Estado</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Ultimo uso</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Creacion</th>
            <th className="border-b border-slate-200 px-3 py-3 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map((apiKey) => (
            <tr key={apiKey.id} className="align-middle text-slate-700">
              <td className="border-b border-slate-100 px-3 py-3 font-medium text-slate-950">{apiKey.nombre}</td>
              <td className="border-b border-slate-100 px-3 py-3 font-mono text-xs">{apiKey.key_prefix}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex max-w-[300px] flex-wrap gap-1.5">
                  {(apiKey.scopes || []).map((scope) => (
                    <Badge key={scope} tone="info" className="font-mono">
                      {scope}
                    </Badge>
                  ))}
                </div>
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <ActiveBadge active={apiKey.activa} />
              </td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(apiKey.ultimo_uso_en)}</td>
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(apiKey.fecha_creacion)}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex justify-end">
                  {canManage && apiKey.activa ? (
                    <Button
                      variant="danger"
                      size="sm"
                      icon={Ban}
                      loading={revokingId === apiKey.id}
                      onClick={() => onRevoke(apiKey)}
                    >
                      Revocar
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
