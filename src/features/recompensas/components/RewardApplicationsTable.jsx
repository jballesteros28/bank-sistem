import { Gift } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatCurrency, formatDateTime, formatNumber } from "../../../shared/utils/formatters";

function formatRewardValue(value, currency) {
  if (currency === "PUNTOS") {
    return `${formatNumber(value)} PUNTOS`;
  }
  return formatCurrency(value, currency);
}

function formatId(value) {
  if (!value) {
    return "-";
  }
  return (
    <span className="font-mono text-xs text-slate-500" title={value}>
      {value.slice(0, 8)}...
    </span>
  );
}

function LoadingRows({ columnsCount }) {
  return (
    <tbody className="divide-y divide-slate-100 bg-white">
      {Array.from({ length: 4 }).map((_, index) => (
        <tr key={index}>
          {Array.from({ length: columnsCount }).map((__, cellIndex) => (
            <td key={cellIndex} className="px-3 py-3">
              <div className="h-4 w-full max-w-32 animate-pulse rounded bg-slate-100" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}

export function RewardApplicationsTable({ applications = [], loading = false, error, onRetry, ruleMap = new Map(), showUser = true }) {
  const columnsCount = showUser ? 8 : 7;

  if (error) {
    return <ErrorState title="No se pudieron cargar las aplicaciones" message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!loading && !applications.length) {
    return (
      <EmptyState
        icon={Gift}
        title="Sin recompensas"
        description="No hay aplicaciones de recompensa para mostrar con los filtros actuales."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-[980px] w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Fecha</th>
              {showUser ? <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Usuario</th> : null}
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Regla</th>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Compra</th>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Recompensa</th>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Moneda</th>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Referencia</th>
              <th className="border-b border-slate-200 px-3 py-3 font-semibold text-slate-700">Movimiento</th>
            </tr>
          </thead>
          {loading ? (
            <LoadingRows columnsCount={columnsCount} />
          ) : (
            <tbody className="divide-y divide-slate-100 bg-white">
              {applications.map((application) => (
                <tr key={application.id} className="text-slate-700">
                  <td className="px-3 py-3 whitespace-nowrap">{formatDateTime(application.fecha_creacion)}</td>
                  {showUser ? <td className="px-3 py-3">{formatId(application.usuario_id)}</td> : null}
                  <td className="px-3 py-3">
                    <span className="font-medium text-slate-900">{ruleMap.get(application.regla_id)?.nombre || formatId(application.regla_id)}</span>
                  </td>
                  <td className="px-3 py-3">{formatNumber(application.monto_compra)}</td>
                  <td className="px-3 py-3 font-semibold text-slate-950">
                    {formatRewardValue(application.monto_recompensa, application.moneda_recompensa)}
                  </td>
                  <td className="px-3 py-3">{application.moneda_recompensa}</td>
                  <td className="max-w-[180px] truncate px-3 py-3" title={application.referencia_externa || ""}>
                    {application.referencia_externa || "-"}
                  </td>
                  <td className="px-3 py-3">{formatId(application.movimiento_id)}</td>
                </tr>
              ))}
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
