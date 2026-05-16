import { Link } from "react-router-dom";
import { CreditCard, KeyRound, Palette, ReceiptText } from "lucide-react";

import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { ROUTES } from "../../../shared/utils/constants";

const actions = [
  { label: "Crear wallet organizacion", to: ROUTES.wallets, icon: CreditCard },
  { label: "Ver movimientos", to: ROUTES.movimientos, icon: ReceiptText },
  { label: "Configurar branding", to: ROUTES.branding, icon: Palette },
  { label: "Gestionar integraciones", to: ROUTES.integraciones, icon: KeyRound },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader title="Accesos rapidos" description="Atajos operativos para las tareas habituales." />
      <div className="grid gap-3 sm:grid-cols-2">
        {actions.map((action) => (
          <Link
            key={action.to}
            className="flex min-h-12 items-center gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-brand-primary hover:text-brand-primary"
            to={action.to}
          >
            <action.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{action.label}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}
