import { Badge } from "../../../shared/components/ui/Badge";
import { getMovementKind, getMovementTypeLabel } from "../movementUtils";

const tones = {
  deposito: "success",
  retiro: "warning",
  transferencia: "info",
  pago: "neutral",
  pago_organizacion: "info",
  cashback: "success",
  ajuste_admin: "warning",
  reversa: "danger",
};

export function MovementTypeBadge({ movement, tipo }) {
  const kind = movement ? getMovementKind(movement) : tipo;
  return <Badge tone={tones[kind] || "neutral"}>{getMovementTypeLabel(kind)}</Badge>;
}
