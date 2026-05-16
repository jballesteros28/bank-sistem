import { Badge } from "../../../shared/components/ui/Badge";
import { getNotificationChannelLabel } from "../notificationUtils";

const tones = {
  interna: "info",
  email: "neutral",
};

export function NotificationChannelBadge({ canal }) {
  return <Badge tone={tones[canal] || "neutral"}>{getNotificationChannelLabel(canal)}</Badge>;
}
