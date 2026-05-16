import { AlertCircle } from "lucide-react";

import { Card } from "../../../shared/components/ui/Card";

export function MetricCard({ title, value, description, icon: Icon, loading = false, error = false }) {
  return (
    <Card>
      <div className="flex min-h-32 items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <div className="mt-3">
            {loading ? (
              <div className="h-8 w-24 animate-pulse rounded-md bg-slate-100" />
            ) : error ? (
              <div className="flex items-center gap-2 text-sm font-medium text-rose-700">
                <AlertCircle className="h-4 w-4" aria-hidden="true" />
                No disponible
              </div>
            ) : (
              <p className="truncate text-2xl font-semibold text-slate-950">{value}</p>
            )}
          </div>
          {description ? <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p> : null}
        </div>
        {Icon ? (
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </div>
        ) : null}
      </div>
    </Card>
  );
}
