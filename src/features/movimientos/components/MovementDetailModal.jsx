import { Modal } from "../../../shared/components/ui/Modal";
import { formatCurrency, formatDateTime } from "../../../shared/utils/formatters";
import { getWalletLabel } from "../movementUtils";
import { MovementStatusBadge } from "./MovementStatusBadge";
import { MovementTypeBadge } from "./MovementTypeBadge";

function DetailItem({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-400">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-slate-800">{children || "-"}</dd>
    </div>
  );
}

export function MovementDetailModal({ movement, walletMap, onClose }) {
  return (
    <Modal open={Boolean(movement)} title="Detalle de movimiento" onClose={onClose}>
      {movement ? (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <MovementTypeBadge movement={movement} />
            <MovementStatusBadge estado={movement.estado} />
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            <DetailItem label="ID">{movement.id}</DetailItem>
            <DetailItem label="Fecha">{formatDateTime(movement.fecha)}</DetailItem>
            <DetailItem label="Monto">{formatCurrency(movement.monto, movement.moneda)}</DetailItem>
            <DetailItem label="Moneda">{movement.moneda}</DetailItem>
            <DetailItem label="Descripcion">{movement.descripcion}</DetailItem>
            <DetailItem label="Referencia externa">{movement.referencia_externa}</DetailItem>
            <DetailItem label="Origen">{getWalletLabel(movement.wallet_origen_id, walletMap)}</DetailItem>
            <DetailItem label="Destino">{getWalletLabel(movement.wallet_destino_id, walletMap)}</DetailItem>
            <DetailItem label="Movimiento origen">{movement.movimiento_origen_id}</DetailItem>
            <DetailItem label="Motivo reversa">{movement.motivo_reversa}</DetailItem>
          </dl>
          {movement.metadata ? (
            <div>
              <p className="text-xs font-medium uppercase text-slate-400">Metadata</p>
              <pre className="mt-2 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify(movement.metadata, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      ) : null}
    </Modal>
  );
}
