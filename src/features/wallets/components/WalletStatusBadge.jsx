import { Badge } from "../../../shared/components/ui/Badge";

const statusMeta = {
  activa: { label: "Activa", tone: "success" },
  inactiva: { label: "Inactiva", tone: "warning" },
  congelada: { label: "Congelada", tone: "danger" },
  cerrada: { label: "Cerrada", tone: "neutral" },
};

export function WalletStatusBadge({ estado }) {
  const meta = statusMeta[estado] || { label: estado || "-", tone: "neutral" };
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}
