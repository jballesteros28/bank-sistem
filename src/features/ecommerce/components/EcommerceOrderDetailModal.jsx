import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { Modal } from "../../../shared/components/ui/Modal";
import { formatDateTime, formatNumber } from "../../../shared/utils/formatters";
import { ecommerceQueryKeys, getEcommerceOrderById } from "../api";
import { EcommerceProviderBadge } from "./EcommerceProviderBadge";
import { EcommerceStatusBadge, ProcessingBadge } from "./EcommerceStatusBadge";

function Field({ label, children }) {
  return (
    <div className="min-w-0 rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <p className="text-xs font-medium uppercase tracking-normal text-slate-400">{label}</p>
      <div className="mt-1 min-h-5 break-words text-sm text-slate-800">{children || <span className="text-slate-400">-</span>}</div>
    </div>
  );
}

function formatJson(value) {
  if (!value) {
    return "No disponible en la respuesta actual.";
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function ShortId({ value }) {
  if (!value) {
    return <span className="text-slate-400">-</span>;
  }

  return <span className="font-mono text-xs text-slate-700">{value}</span>;
}

export function EcommerceOrderDetailModal({ order, onClose }) {
  const detailQuery = useQuery({
    queryKey: ecommerceQueryKeys.order(order?.id),
    queryFn: () => getEcommerceOrderById(order.id),
    enabled: Boolean(order?.id),
    retry: false,
  });

  const detail = detailQuery.data || order;
  const rawPayload = detail?.raw_payload;

  return (
    <Modal open={Boolean(order)} title="Detalle de orden ecommerce" onClose={onClose} panelClassName="max-w-3xl">
      {detailQuery.isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-14 animate-pulse rounded-md bg-slate-100" />
          ))}
        </div>
      ) : null}

      {detailQuery.error ? (
        <ErrorState
          title="No se pudo cargar el detalle"
          message={getApiErrorMessage(detailQuery.error)}
          onRetry={() => detailQuery.refetch()}
        />
      ) : null}

      {!detailQuery.isLoading && !detailQuery.error && detail ? (
        <div className="space-y-5">
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="ID">
              <ShortId value={detail.id} />
            </Field>
            <Field label="Organizacion">
              <ShortId value={detail.organizacion_id} />
            </Field>
            <Field label="Proveedor">
              <EcommerceProviderBadge provider={detail.proveedor} />
            </Field>
            <Field label="External order ID">{detail.external_order_id}</Field>
            <Field label="Customer email">{detail.customer_email}</Field>
            <Field label="Customer name">{detail.customer_name}</Field>
            <Field label="Amount">{formatNumber(detail.amount)}</Field>
            <Field label="Currency">{detail.currency}</Field>
            <Field label="Status">
              <EcommerceStatusBadge status={detail.status} />
            </Field>
            <Field label="Procesado">
              <ProcessingBadge order={detail} />
            </Field>
            <Field label="Fecha creacion">{formatDateTime(detail.fecha_creacion)}</Field>
            <Field label="Fecha procesamiento">{formatDateTime(detail.fecha_procesamiento)}</Field>
          </div>

          <div className="rounded-md border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-slate-950">Recompensa</p>
            {detail.recompensa_aplicada_id ? (
              <div className="mt-2 space-y-2 text-sm text-slate-700">
                <p>
                  ID aplicado: <ShortId value={detail.recompensa_aplicada_id} />
                </p>
                <Link to="/recompensas" className="font-medium text-brand-primary hover:underline">
                  Ver en Recompensas
                </Link>
              </div>
            ) : (
              <p className="mt-2 text-sm text-slate-600">{detail.error_procesamiento || "Sin recompensa aplicada."}</p>
            )}
          </div>

          <Field label="Error procesamiento">{detail.error_procesamiento}</Field>

          <div>
            <p className="mb-2 text-sm font-semibold text-slate-950">Raw payload</p>
            <pre className="max-h-80 overflow-auto rounded-lg border border-slate-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100">
              <code>{formatJson(rawPayload)}</code>
            </pre>
          </div>
        </div>
      ) : null}

      <div className="mt-5 flex justify-end">
        <Button variant="secondary" onClick={onClose}>
          Cerrar
        </Button>
      </div>
    </Modal>
  );
}
