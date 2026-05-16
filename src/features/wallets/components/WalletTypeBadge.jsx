import { Badge } from "../../../shared/components/ui/Badge";

const typeMeta = {
  principal: { label: "Principal", tone: "info" },
  ahorro: { label: "Ahorro", tone: "neutral" },
  empresa: { label: "Empresa", tone: "info" },
  operativa: { label: "Operativa", tone: "success" },
  caja: { label: "Caja", tone: "warning" },
  recompensas: { label: "Recompensas", tone: "neutral" },
};

export function WalletTypeBadge({ tipo }) {
  const meta = typeMeta[tipo] || { label: tipo || "-", tone: "neutral" };
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}
