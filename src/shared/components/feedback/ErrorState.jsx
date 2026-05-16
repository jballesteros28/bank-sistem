import { AlertCircle } from "lucide-react";

import { Button } from "../ui/Button";

export function ErrorState({ title = "No se pudo cargar", message = "Intenta nuevamente en unos segundos.", onRetry }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-5">
      <div className="flex gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" aria-hidden="true" />
        <div>
          <h3 className="text-sm font-semibold text-rose-900">{title}</h3>
          <p className="mt-1 text-sm text-rose-700">{message}</p>
          {onRetry ? (
            <Button className="mt-4" variant="secondary" size="sm" onClick={onRetry}>
              Reintentar
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
