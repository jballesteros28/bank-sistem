import { Loader2 } from "lucide-react";

export function LoadingScreen({ label = "Cargando" }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm">
        <Loader2 className="h-4 w-4 animate-spin text-brand-primary" aria-hidden="true" />
        <span>{label}</span>
      </div>
    </div>
  );
}
