import { Modal } from "../../../shared/components/ui/Modal";
import { formatDateTime } from "../../../shared/utils/formatters";
import { NotificationChannelBadge } from "./NotificationChannelBadge";
import { NotificationTypeBadge } from "./NotificationTypeBadge";

function DetailItem({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-400">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-slate-800">{children || "-"}</dd>
    </div>
  );
}

export function NotificationDetailModal({ notification, onClose }) {
  return (
    <Modal open={Boolean(notification)} title="Detalle de notificacion" onClose={onClose}>
      {notification ? (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <NotificationTypeBadge tipo={notification.tipo} />
            <NotificationChannelBadge canal={notification.canal} />
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            <DetailItem label="ID">{notification.id}</DetailItem>
            <DetailItem label="Estado">{notification.leida ? "Leida" : "No leida"}</DetailItem>
            <DetailItem label="Titulo">{notification.titulo}</DetailItem>
            <DetailItem label="Tipo">{notification.tipo}</DetailItem>
            <DetailItem label="Canal">{notification.canal}</DetailItem>
            <DetailItem label="Fecha creacion">{formatDateTime(notification.fecha_creacion)}</DetailItem>
            <DetailItem label="Fecha lectura">{formatDateTime(notification.fecha_lectura)}</DetailItem>
            <DetailItem label="Fecha envio">{formatDateTime(notification.fecha_envio)}</DetailItem>
            <DetailItem label="Enviada">{notification.enviada ? "Si" : "No"}</DetailItem>
            <DetailItem label="Error envio">{notification.error_envio}</DetailItem>
            <div className="sm:col-span-2">
              <DetailItem label="Mensaje">{notification.mensaje}</DetailItem>
            </div>
          </dl>
          {notification.metadata ? (
            <div>
              <p className="text-xs font-medium uppercase text-slate-400">Metadata</p>
              <pre className="mt-2 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify(notification.metadata, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      ) : null}
    </Modal>
  );
}
