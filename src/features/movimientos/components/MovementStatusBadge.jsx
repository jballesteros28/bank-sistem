import { Badge } from "../../../shared/components/ui/Badge";
import { getMovementStatusLabel } from "../movementUtils";

const tones = {
  pendiente: "warning",
  aprobada: "success",
  rechazada: "danger",
  cancelada: "neutral",
  revertida: "danger",
};

export function MovementStatusBadge({ estado }) {
  return <Badge tone={tones[estado] || "neutral"}>{getMovementStatusLabel(estado)}</Badge>;
}
