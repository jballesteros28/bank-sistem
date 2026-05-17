import { Badge } from "../../../shared/components/ui/Badge";
import { getProcessingState, getStatusLabel } from "../schemas";

const statusTones = {
  paid: "success",
  cancelled: "neutral",
  refunded: "info",
};

const processingConfig = {
  procesado: { tone: "success", label: "Procesado" },
  error: { tone: "danger", label: "Error" },
  pendiente: { tone: "warning", label: "Pendiente" },
};

export function EcommerceStatusBadge({ status }) {
  return <Badge tone={statusTones[status] || "neutral"}>{getStatusLabel(status)}</Badge>;
}

export function ProcessingBadge({ order }) {
  const state = getProcessingState(order);
  const config = processingConfig[state] || processingConfig.pendiente;

  return <Badge tone={config.tone}>{config.label}</Badge>;
}
