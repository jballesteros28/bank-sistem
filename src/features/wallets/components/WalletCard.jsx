import { Building2, Star, UserRound, WalletCards } from "lucide-react";

import { Badge } from "../../../shared/components/ui/Badge";
import { formatCurrency, formatDate } from "../../../shared/utils/formatters";
import { WalletStatusBadge } from "./WalletStatusBadge";
import { WalletTypeBadge } from "./WalletTypeBadge";

function ownerLabel(ownerType) {
  if (ownerType === "organizacion") {
    return "Organizacion";
  }
  if (ownerType === "usuario") {
    return "Usuario";
  }
  return ownerType || "-";
}

function limitLabel(wallet) {
  if (wallet?.limite_operacion === null || wallet?.limite_operacion === undefined) {
    return "Sin limite";
  }
  return formatCurrency(wallet.limite_operacion, wallet.moneda);
}

export function WalletCard({ wallet, featured = false }) {
  const OwnerIcon = wallet?.owner_type === "organizacion" ? Building2 : UserRound;

  return (
    <article
      className={[
        "rounded-lg border bg-white p-5 shadow-sm",
        featured ? "border-brand-primary/40 ring-1 ring-brand-primary/10" : "border-slate-200",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <OwnerIcon className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
            <p className="truncate text-base font-semibold text-slate-950">{wallet.alias || "Wallet sin alias"}</p>
          </div>
          <p className="mt-1 text-sm text-slate-500">{ownerLabel(wallet.owner_type)}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
          <WalletCards className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-medium uppercase text-slate-400">Saldo</p>
        <p className="mt-1 text-2xl font-semibold text-slate-950">{formatCurrency(wallet.saldo, wallet.moneda)}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <WalletStatusBadge estado={wallet.estado} />
        <WalletTypeBadge tipo={wallet.tipo} />
        <Badge tone="neutral">{wallet.moneda || "-"}</Badge>
        {wallet.es_principal ? (
          <Badge tone="info" className="gap-1">
            <Star className="h-3 w-3" aria-hidden="true" />
            Principal
          </Badge>
        ) : null}
      </div>

      <dl className="mt-5 grid gap-3 border-t border-slate-100 pt-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase text-slate-400">Owner</dt>
          <dd className="mt-1 font-medium text-slate-700">{ownerLabel(wallet.owner_type)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-slate-400">Limite operacion</dt>
          <dd className="mt-1 font-medium text-slate-700">{limitLabel(wallet)}</dd>
        </div>
        {wallet.fecha_creacion ? (
          <div className="sm:col-span-2">
            <dt className="text-xs font-medium uppercase text-slate-400">Fecha creacion</dt>
            <dd className="mt-1 font-medium text-slate-700">{formatDate(wallet.fecha_creacion)}</dd>
          </div>
        ) : null}
      </dl>
    </article>
  );
}
