import { CreditCard, Layers3, ReceiptText, WalletCards } from "lucide-react";

import { Card } from "../../../shared/components/ui/Card";
import { formatCurrency } from "../../../shared/utils/formatters";

const metrics = [
  { label: "Saldo total", value: formatCurrency(0), icon: WalletCards },
  { label: "Movimientos", value: "0", icon: ReceiptText },
  { label: "Wallets", value: "0", icon: CreditCard },
  { label: "Plan actual", value: "Free", icon: Layers3 },
];

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Resumen operativo de la organizacion.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">{metric.label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-950">{metric.value}</p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
                <metric.icon className="h-5 w-5" aria-hidden="true" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
