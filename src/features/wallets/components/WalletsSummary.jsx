import { Building2, UserRound, WalletCards } from "lucide-react";

import { formatCurrency, formatNumber } from "../../../shared/utils/formatters";

function SummaryItem({ title, value, description, icon: Icon, loading = false }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          {loading ? (
            <div className="mt-3 h-7 w-24 animate-pulse rounded bg-slate-100" />
          ) : (
            <p className="mt-2 truncate text-2xl font-semibold text-slate-950">{value}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

export function WalletsSummary({
  principalWallet,
  organizationWallets = [],
  userWallets = [],
  canViewOrganization = false,
  organizationLoading = false,
  principalLoading = false,
  userLoading = false,
}) {
  const principalValue = principalWallet ? formatCurrency(principalWallet.saldo, principalWallet.moneda) : "-";
  const principalDescription = canViewOrganization ? principalWallet?.alias || "Wallet principal" : "Seccion bloqueada";

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <SummaryItem
        title="Saldo principal"
        value={principalValue}
        description={principalDescription}
        icon={WalletCards}
        loading={principalLoading}
      />
      <SummaryItem
        title="Wallets organizacion"
        value={canViewOrganization ? formatNumber(organizationWallets.length) : "-"}
        description={canViewOrganization ? "Visibles para tu rol" : "Sin permisos de consulta"}
        icon={Building2}
        loading={organizationLoading}
      />
      <SummaryItem
        title="Wallets usuario"
        value={formatNumber(userWallets.length)}
        description="Wallets visibles por permisos"
        icon={UserRound}
        loading={userLoading}
      />
    </div>
  );
}
