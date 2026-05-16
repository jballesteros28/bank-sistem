import { Eye, RotateCcw } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatCurrency, formatDateTime } from "../../../shared/utils/formatters";
import { getWalletLabel } from "../movementUtils";
import { MovementStatusBadge } from "./MovementStatusBadge";
import { MovementTypeBadge } from "./MovementTypeBadge";

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
      ))}
    </div>
  );
}

function canReverseRow(movement, canReverse) {
  return canReverse && movement.estado === "aprobada" && movement.tipo !== "reversa" && !movement.es_reversa;
}

export function MovementsTable({
  movements = [],
  walletMap,
  loading = false,
  error,
  onRetry,
  onView,
  onReverse,
  canReverse = false,
}) {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!movements.length) {
    return <EmptyState title="Todavia no hay movimientos" description="Cuando existan operaciones, apareceran en esta tabla." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[1040px] w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-slate-400">
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Fecha</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Tipo</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Monto</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Moneda</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Estado</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Descripcion</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Origen</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Destino</th>
            <th className="border-b border-slate-200 px-3 py-3 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {movements.map((movement) => (
            <tr key={movement.id} className="align-middle text-slate-700">
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(movement.fecha)}</td>
              <td className="border-b border-slate-100 px-3 py-3"><MovementTypeBadge movement={movement} /></td>
              <td className="border-b border-slate-100 px-3 py-3 font-semibold text-slate-950">{formatCurrency(movement.monto, movement.moneda)}</td>
              <td className="border-b border-slate-100 px-3 py-3">{movement.moneda}</td>
              <td className="border-b border-slate-100 px-3 py-3"><MovementStatusBadge estado={movement.estado} /></td>
              <td className="max-w-[220px] truncate border-b border-slate-100 px-3 py-3">{movement.descripcion || movement.referencia_externa || "-"}</td>
              <td className="max-w-[180px] truncate border-b border-slate-100 px-3 py-3">{getWalletLabel(movement.wallet_origen_id, walletMap)}</td>
              <td className="max-w-[180px] truncate border-b border-slate-100 px-3 py-3">{getWalletLabel(movement.wallet_destino_id, walletMap)}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex justify-end gap-2">
                  <Button variant="secondary" size="sm" icon={Eye} onClick={() => onView(movement)}>
                    Ver
                  </Button>
                  {canReverseRow(movement, canReverse) ? (
                    <Button variant="secondary" size="sm" icon={RotateCcw} onClick={() => onReverse(movement)}>
                      Revertir
                    </Button>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
