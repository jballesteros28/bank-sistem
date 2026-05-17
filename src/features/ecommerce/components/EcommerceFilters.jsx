import { Search, X } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { ECOMMERCE_PROVIDERS, ECOMMERCE_STATUSES, PROCESSING_STATES } from "../schemas";

function hasActiveFilters(filters) {
  return Boolean(filters.search || filters.proveedor || filters.status || filters.processing);
}

export function EcommerceFilters({ filters, onChange }) {
  const updateFilter = (field, value) => {
    onChange({ ...filters, [field]: value });
  };

  const clearFilters = () => {
    onChange({ search: "", proveedor: "", status: "", processing: "" });
  };

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 xl:flex-row xl:items-end">
      <div className="grid flex-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Buscar</span>
          <span className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              className="block h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
              value={filters.search}
              onChange={(event) => updateFilter("search", event.target.value)}
              placeholder="Email u order id"
            />
          </span>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Proveedor</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.proveedor}
            onChange={(event) => updateFilter("proveedor", event.target.value)}
          >
            <option value="">Todos</option>
            {ECOMMERCE_PROVIDERS.map((provider) => (
              <option key={provider.value} value={provider.value}>
                {provider.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Status</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.status}
            onChange={(event) => updateFilter("status", event.target.value)}
          >
            <option value="">Todos</option>
            {ECOMMERCE_STATUSES.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Procesamiento</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.processing}
            onChange={(event) => updateFilter("processing", event.target.value)}
          >
            <option value="">Todos</option>
            {PROCESSING_STATES.map((state) => (
              <option key={state.value} value={state.value}>
                {state.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {hasActiveFilters(filters) ? (
        <Button variant="secondary" size="sm" icon={X} onClick={clearFilters} className="xl:mb-0.5">
          Limpiar
        </Button>
      ) : null}
    </div>
  );
}
