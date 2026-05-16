import { Badge } from "../../../shared/components/ui/Badge";
import { getUsuarioStatus } from "../schemas";

const statusMeta = {
  activo: { label: "Activo", tone: "success" },
  inactivo: { label: "Inactivo", tone: "warning" },
  suspendido: { label: "Suspendido", tone: "danger" },
};

export function UserStatusBadge({ usuario, estado }) {
  const status = estado || getUsuarioStatus(usuario);
  const meta = statusMeta[status] || { label: status || "-", tone: "neutral" };
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}
