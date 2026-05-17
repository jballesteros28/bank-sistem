import { Badge } from "../../../shared/components/ui/Badge";
import { getRewardStatusLabel } from "../schemas";

const tones = {
  activa: "success",
  inactiva: "neutral",
  pausada: "warning",
};

export function RewardRuleStatusBadge({ status }) {
  return <Badge tone={tones[status] || "neutral"}>{getRewardStatusLabel(status)}</Badge>;
}
