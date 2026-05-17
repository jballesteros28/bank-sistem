import { WalletCards } from "lucide-react";

import { getApiErrorMessage } from "../../../../shared/api/apiError";
import { Card, CardHeader } from "../../../../shared/components/ui/Card";
import { EmptyState } from "../../../../shared/components/ui/EmptyState";
import { formatCurrency } from "../../../../shared/utils/formatters";
import { WalletStatusBadge } from "../../../wallets/components/WalletStatusBadge";
import { WalletTypeBadge } from "../../../wallets/components/WalletTypeBadge";

export function ClientWalletCard({ wallet, loading, error, onRetry }) {
  return (
    <Card>
      <CardHeader title="Mi wallet" description="Saldo disponible para pagos dentro de la organizacion." />
      {loading ? (
        <div className="space-y-4">
          <div className="h-7 w-40 animate-pulse rounded-md bg-slate-100" />
          <div className="h-16 animate-pulse rounded-md bg-slate-100" />
          <div className="h-8 w-56 animate-pulse rounded-md bg-slate-100" />
        </div>
      ) : null}
      {!loading && error ? (
        <div className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
          {getApiErrorMessage(error)}
          {onRetry ? (
            <button className="ml-2 text-rose-900 underline" type="button" onClick={onRetry}>
              Reintentar
            </button>
          ) : null}
        </div>
      ) : null}
      {!loading && !error && !wallet ? (
        <EmptyState title="Todavia no tenes wallet asignada." description="Cuando tu organizacion cree una wallet para tu usuario, va a aparecer aca." />
      ) : null}
      {!loading && !error && wallet ? (
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="truncate text-lg font-semibold text-slate-950">{wallet.alias || "Wallet principal"}</p>
              <p className="mt-1 text-sm text-slate-500">{wallet.moneda}</p>
            </div>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
              <WalletCards className="h-5 w-5" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">Saldo</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{formatCurrency(wallet.saldo, wallet.moneda)}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <WalletStatusBadge estado={wallet.estado} />
            <WalletTypeBadge tipo={wallet.tipo} />
          </div>
        </div>
      ) : null}
    </Card>
  );
}
