import { Users, WalletCards, ReceiptText } from "lucide-react";

import { formatLimit } from "../../../shared/utils/formatters";

function LimitItem({ label, value, icon: Icon }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{formatLimit(value)}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

export function PlanLimitsCard({ plan }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <LimitItem label="Usuarios" value={plan?.limite_usuarios} icon={Users} />
      <LimitItem label="Wallets" value={plan?.limite_wallets} icon={WalletCards} />
      <LimitItem label="Movimientos mes" value={plan?.limite_movimientos_mes} icon={ReceiptText} />
    </div>
  );
}
