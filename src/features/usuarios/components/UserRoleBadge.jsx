import { Badge } from "../../../shared/components/ui/Badge";
import { humanizeRole } from "../../../shared/utils/formatters";

const roleTones = {
  super_admin: "danger",
  owner: "warning",
  admin: "info",
  soporte: "neutral",
  cliente: "success",
};

export function UserRoleBadge({ rol }) {
  return <Badge tone={roleTones[rol] || "neutral"}>{humanizeRole(rol)}</Badge>;
}
