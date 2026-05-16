import { Plus, Search } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { userRoleOptions, userStatusFilterOptions } from "../schemas";

export function UsersToolbar({ filters, onChange, onCreate, canCreate }) {
  const updateFilter = (field, value) => {
    onChange({ ...filters, [field]: value });
  };

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm xl:flex-row xl:items-end xl:justify-between">
      <div className="grid flex-1 gap-3 md:grid-cols-3">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Rol</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.rol}
            onChange={(event) => updateFilter("rol", event.target.value)}
          >
            <option value="">Todos</option>
            {userRoleOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Estado</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.estado}
            onChange={(event) => updateFilter("estado", event.target.value)}
          >
            <option value="">Todos</option>
            {userStatusFilterOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Buscar</span>
          <span className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              className="block h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
              value={filters.search}
              onChange={(event) => updateFilter("search", event.target.value)}
              placeholder="Nombre o email"
            />
          </span>
        </label>
      </div>
      {canCreate ? (
        <Button icon={Plus} onClick={onCreate} className="xl:mb-0">
          Crear usuario
        </Button>
      ) : null}
    </div>
  );
}
