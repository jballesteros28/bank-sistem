import { Badge } from "../../../shared/components/ui/Badge";

const tones = {
  free: "neutral",
  starter: "info",
  pro: "success",
  enterprise: "warning",
};

export function PlanBadge({ plan, current = false }) {
  return (
    <Badge tone={current ? "success" : tones[plan?.codigo] || "neutral"}>
      {current ? "Plan actual" : plan?.activo === false ? "Inactivo" : plan?.nombre || "-"}
    </Badge>
  );
}
