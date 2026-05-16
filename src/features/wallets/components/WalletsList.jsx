import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { WalletCard } from "./WalletCard";

function WalletSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="h-5 w-36 animate-pulse rounded bg-slate-100" />
          <div className="h-4 w-24 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="h-10 w-10 animate-pulse rounded-md bg-slate-100" />
      </div>
      <div className="mt-6 h-8 w-44 animate-pulse rounded bg-slate-100" />
      <div className="mt-5 flex gap-2">
        <div className="h-7 w-20 animate-pulse rounded-full bg-slate-100" />
        <div className="h-7 w-24 animate-pulse rounded-full bg-slate-100" />
      </div>
      <div className="mt-6 h-16 animate-pulse rounded bg-slate-100" />
    </div>
  );
}

export function WalletsList({
  wallets = [],
  loading = false,
  error,
  emptyTitle = "Sin wallets",
  emptyDescription = "Todavia no hay wallets disponibles para esta seccion.",
  onRetry,
  featured = false,
}) {
  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <WalletSkeleton key={item} />
        ))}
      </div>
    );
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!wallets.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
      {wallets.map((wallet) => (
        <WalletCard key={wallet.id} wallet={wallet} featured={featured || wallet.es_principal} />
      ))}
    </div>
  );
}
