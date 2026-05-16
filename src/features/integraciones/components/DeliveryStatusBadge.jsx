import { Badge } from "../../../shared/components/ui/Badge";

const statusLabels = {
  pendiente: "Pendiente",
  enviado: "Enviado",
  fallido: "Fallido",
};

const statusTones = {
  pendiente: "warning",
  enviado: "success",
  fallido: "danger",
};

export function DeliveryStatusBadge({ status }) {
  return <Badge tone={statusTones[status] || "neutral"}>{statusLabels[status] || status || "-"}</Badge>;
}
