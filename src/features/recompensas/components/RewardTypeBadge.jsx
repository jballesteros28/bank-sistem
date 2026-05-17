import { Badge } from "../../../shared/components/ui/Badge";
import { getRewardTypeLabel } from "../schemas";

const tones = {
  cashback: "success",
  puntos: "info",
  credito_tienda: "warning",
};

export function RewardTypeBadge({ type }) {
  return <Badge tone={tones[type] || "neutral"}>{getRewardTypeLabel(type)}</Badge>;
}
