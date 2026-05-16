import { Check, Eye, MailCheck, MailWarning } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { Badge } from "../../../shared/components/ui/Badge";
import { formatDateTime } from "../../../shared/utils/formatters";
import { NotificationChannelBadge } from "./NotificationChannelBadge";
import { NotificationTypeBadge } from "./NotificationTypeBadge";

function EmailStatus({ notification }) {
  if (notification.canal !== "email") {
    return null;
  }
  if (notification.error_envio) {
    return (
      <Badge tone="danger" className="gap-1">
        <MailWarning className="h-3 w-3" aria-hidden="true" />
        Error envio
      </Badge>
    );
  }
  if (notification.enviada) {
    return (
      <Badge tone="success" className="gap-1">
        <MailCheck className="h-3 w-3" aria-hidden="true" />
        Enviada
      </Badge>
    );
  }
  return <Badge tone="warning">Pendiente envio</Badge>;
}

export function NotificationCard({ notification, onView, onMarkRead, markingRead = false }) {
  return (
    <article
      className={[
        "rounded-lg border bg-white p-5 shadow-sm",
        notification.leida ? "border-slate-200" : "border-brand-primary/40 ring-1 ring-brand-primary/10",
      ].join(" ")}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap gap-2">
            <NotificationTypeBadge tipo={notification.tipo} />
            <NotificationChannelBadge canal={notification.canal} />
            <Badge tone={notification.leida ? "neutral" : "success"}>{notification.leida ? "Leida" : "No leida"}</Badge>
            <EmailStatus notification={notification} />
          </div>
          <h3 className="mt-3 text-base font-semibold text-slate-950">{notification.titulo}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-slate-500">{notification.mensaje}</p>
          <p className="mt-3 text-xs font-medium text-slate-400">{formatDateTime(notification.fecha_creacion)}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button variant="secondary" size="sm" icon={Eye} onClick={() => onView(notification)}>
            Ver
          </Button>
          {!notification.leida ? (
            <Button variant="secondary" size="sm" icon={Check} loading={markingRead} onClick={() => onMarkRead(notification)}>
              Marcar leida
            </Button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
