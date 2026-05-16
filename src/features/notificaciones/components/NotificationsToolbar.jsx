import { Search } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { notificationChannelOptions, notificationTypeOptions } from "../notificationUtils";

export function NotificationsToolbar({
  filters,
  onChange,
  scope,
  onScopeChange,
  canViewOrganization = false,
  onMarkAllRead,
  markingAll = false,
  unreadCount = 0,
}) {
  const updateFilter = (field, value) => {
    onChange({ ...filters, [field]: value });
  };

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={[
              "rounded-md px-3 py-2 text-sm font-medium ring-1 transition",
              scope === "me" ? "bg-brand-primary text-white ring-brand-primary" : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50",
            ].join(" ")}
            onClick={() => onScopeChange("me")}
          >
            Mis notificaciones
          </button>
          {canViewOrganization ? (
            <button
              type="button"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium ring-1 transition",
                scope === "organization"
                  ? "bg-brand-primary text-white ring-brand-primary"
                  : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50",
              ].join(" ")}
              onClick={() => onScopeChange("organization")}
            >
              Organizacion
            </button>
          ) : null}
        </div>
        <Button variant="secondary" onClick={onMarkAllRead} loading={markingAll} disabled={unreadCount < 1}>
          Marcar todas como leidas
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Estado</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.readStatus}
            onChange={(event) => updateFilter("readStatus", event.target.value)}
          >
            <option value="">Todas</option>
            <option value="unread">No leidas</option>
            <option value="read">Leidas</option>
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Tipo</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.tipo}
            onChange={(event) => updateFilter("tipo", event.target.value)}
          >
            <option value="">Todos</option>
            {notificationTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Canal</span>
          <select
            className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
            value={filters.canal}
            onChange={(event) => updateFilter("canal", event.target.value)}
          >
            <option value="">Todos</option>
            {notificationChannelOptions.map((option) => (
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
              placeholder="Titulo o mensaje"
            />
          </span>
        </label>
      </div>
    </div>
  );
}
