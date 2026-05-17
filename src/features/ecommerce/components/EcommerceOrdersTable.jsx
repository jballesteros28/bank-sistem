import { Eye } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { formatDateTime, formatNumber } from "../../../shared/utils/formatters";
import { EcommerceEmptyState } from "./EcommerceEmptyState";
import { EcommerceProviderBadge } from "./EcommerceProviderBadge";
import { EcommerceStatusBadge, ProcessingBadge } from "./EcommerceStatusBadge";

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
      ))}
    </div>
  );
}

function ShortId({ value }) {
  if (!value) {
    return <span className="text-slate-400">-</span>;
  }

  return (
    <span className="font-mono text-xs text-slate-600" title={value}>
      {value.slice(0, 8)}...
    </span>
  );
}

export function EcommerceOrdersTable({
  orders = [],
  loading = false,
  error,
  onRetry,
  onView,
  emptyTitle,
  emptyDescription,
}) {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return <ErrorState title="No se pudieron cargar las ordenes ecommerce" message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!orders.length) {
    return <EcommerceEmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[1360px] w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-slate-400">
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Fecha</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Proveedor</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">External order</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Customer email</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Amount</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Currency</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Status</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Procesado</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Recompensa</th>
            <th className="border-b border-slate-200 px-3 py-3 font-semibold">Error</th>
            <th className="border-b border-slate-200 px-3 py-3 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id} className="align-middle text-slate-700">
              <td className="border-b border-slate-100 px-3 py-3 whitespace-nowrap">{formatDateTime(order.fecha_creacion)}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <EcommerceProviderBadge provider={order.proveedor} />
              </td>
              <td className="max-w-[190px] truncate border-b border-slate-100 px-3 py-3 font-medium text-slate-950" title={order.external_order_id}>
                {order.external_order_id}
              </td>
              <td className="max-w-[230px] truncate border-b border-slate-100 px-3 py-3" title={order.customer_email}>
                {order.customer_email}
              </td>
              <td className="border-b border-slate-100 px-3 py-3 font-semibold text-slate-950">{formatNumber(order.amount)}</td>
              <td className="border-b border-slate-100 px-3 py-3">{order.currency}</td>
              <td className="border-b border-slate-100 px-3 py-3">
                <EcommerceStatusBadge status={order.status} />
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <ProcessingBadge order={order} />
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <ShortId value={order.recompensa_aplicada_id} />
              </td>
              <td className="max-w-[260px] truncate border-b border-slate-100 px-3 py-3" title={order.error_procesamiento || ""}>
                {order.error_procesamiento || <span className="text-slate-400">-</span>}
              </td>
              <td className="border-b border-slate-100 px-3 py-3">
                <div className="flex justify-end">
                  <Button variant="secondary" size="sm" icon={Eye} onClick={() => onView(order)}>
                    Ver detalle
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
