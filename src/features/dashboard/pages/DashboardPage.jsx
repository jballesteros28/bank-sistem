import { Bell, CreditCard, Layers3, ReceiptText } from "lucide-react";

import { useBranding } from "../../organizacion/api";
import { Card } from "../../../shared/components/ui/Card";
import { useAuth } from "../../../shared/hooks/useAuth";
import { humanizeRole } from "../../../shared/utils/formatters";

const dashboardCards = [
  { label: "Wallets", value: "Preparado", icon: CreditCard, description: "Vista operativa para wallets del tenant." },
  { label: "Movimientos", value: "Preparado", icon: ReceiptText, description: "Historial y operaciones internas." },
  { label: "Plan actual", value: "Free", icon: Layers3, description: "Placeholder hasta conectar metricas reales." },
  { label: "Notificaciones", value: "Preparado", icon: Bell, description: "Eventos internos de la organizacion." },
];

export function DashboardPage() {
  const { user } = useAuth();
  const brandingQuery = useBranding();
  const branding = brandingQuery.data;
  const organizationName =
    branding?.nombre_comercial ||
    branding?.nombre ||
    (user?.organizacion_id ? `Org ${String(user.organizacion_id).slice(0, 8)}` : "Organizacion actual");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Hola, {user?.nombre || "usuario"}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {humanizeRole(user?.rol)} · {organizationName}
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardCards.map((card) => (
          <Card key={card.label}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">{card.label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-950">{card.value}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{card.description}</p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
                <card.icon className="h-5 w-5" aria-hidden="true" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
