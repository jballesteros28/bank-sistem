import { Link } from "react-router-dom";
import { ArrowRight, WalletCards } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { Badge } from "../../../shared/components/ui/Badge";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { ROUTES } from "../../../shared/utils/constants";
import { formatCurrency } from "../../../shared/utils/formatters";

function humanize(value) {
  return String(value || "-").replace(/_/g, " ");
}

export function OrganizationWalletCard({ wallet, loading, error }) {
  return (
    <Card>
      <CardHeader title="Wallet principal" description="Saldo operativo de la organizacion." />
      {loading ? (
        <div className="space-y-4">
          <div className="h-8 w-40 animate-pulse rounded-md bg-slate-100" />
          <div className="h-16 animate-pulse rounded-md bg-slate-100" />
        </div>
      ) : null}
      {!loading && error ? <p className="text-sm text-rose-700">{getApiErrorMessage(error)}</p> : null}
      {!loading && !error && wallet ? (
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="truncate text-lg font-semibold text-slate-950">{wallet.alias || "Wallet empresa"}</p>
              <p className="mt-1 text-sm text-slate-500">{humanize(wallet.tipo)} - {wallet.moneda}</p>
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
            <Badge tone={wallet.estado === "activa" ? "success" : "warning"}>{humanize(wallet.estado)}</Badge>
            {wallet.es_principal ? <Badge tone="info">Principal</Badge> : null}
          </div>
          <Link
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-white px-4 text-sm font-medium text-slate-900 ring-1 ring-slate-200 transition hover:bg-slate-50"
            to={ROUTES.wallets}
          >
            Ver wallets
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      ) : null}
    </Card>
  );
}
