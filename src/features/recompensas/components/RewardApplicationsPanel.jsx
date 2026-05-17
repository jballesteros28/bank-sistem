import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { getRewardApplications, getRewardRules, rewardQueryKeys } from "../api";
import { rewardCurrencyOptions } from "../schemas";
import { RewardApplicationsTable } from "./RewardApplicationsTable";

const initialFilters = {
  search: "",
  moneda: "",
  regla_id: "",
};

const emptyArray = [];

function filterApplications(applications, filters, ruleMap) {
  const search = filters.search.trim().toLowerCase();

  return applications.filter((application) => {
    const rule = ruleMap.get(application.regla_id);
    const currencyMatches = !filters.moneda || application.moneda_recompensa === filters.moneda;
    const ruleMatches = !filters.regla_id || application.regla_id === filters.regla_id;
    const searchTarget = [
      application.referencia_externa,
      application.usuario_id,
      application.wallet_destino_id,
      application.movimiento_id,
      application.regla_id,
      rule?.nombre,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchMatches = !search || searchTarget.includes(search);
    return currencyMatches && ruleMatches && searchMatches;
  });
}

export function RewardApplicationsPanel({ user, canView = true }) {
  const [filters, setFilters] = useState(initialFilters);
  const organizationId = user?.organizacion_id || "global";

  const applicationsQuery = useQuery({
    queryKey: rewardQueryKeys.rewardApplications(organizationId, { skip: 0, limit: 100 }),
    queryFn: () => getRewardApplications({ skip: 0, limit: 100 }),
    enabled: canView,
    retry: false,
  });

  const rulesQuery = useQuery({
    queryKey: rewardQueryKeys.rewardRules(organizationId),
    queryFn: () => getRewardRules(),
    enabled: canView,
    retry: false,
  });

  const rules = rulesQuery.data || emptyArray;
  const applications = applicationsQuery.data || emptyArray;
  const ruleMap = useMemo(() => new Map(rules.map((rule) => [rule.id, rule])), [rules]);
  const filteredApplications = useMemo(
    () => filterApplications(applications, filters, ruleMap),
    [applications, filters, ruleMap],
  );

  const updateFilter = (field, value) => {
    setFilters((current) => ({ ...current, [field]: value }));
  };

  return (
    <Card>
      <CardHeader title="Aplicaciones de recompensa" description="Recompensas acreditadas por reglas de loyalty y credito interno." />

      {!canView ? (
        <EmptyState title="Sin permisos" description="Tu rol no puede consultar aplicaciones de recompensa." />
      ) : (
        <div className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">Buscar</span>
              <span className="relative block">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  className="block h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                  value={filters.search}
                  onChange={(event) => updateFilter("search", event.target.value)}
                  placeholder="Referencia o usuario"
                />
              </span>
            </label>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">Moneda</span>
              <select
                className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                value={filters.moneda}
                onChange={(event) => updateFilter("moneda", event.target.value)}
              >
                <option value="">Todas</option>
                {rewardCurrencyOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-slate-700">Regla</span>
              <select
                className="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20"
                value={filters.regla_id}
                onChange={(event) => updateFilter("regla_id", event.target.value)}
                disabled={rulesQuery.isLoading || Boolean(rulesQuery.error)}
              >
                <option value="">Todas</option>
                {rules.map((rule) => (
                  <option key={rule.id} value={rule.id}>
                    {rule.nombre}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {rulesQuery.error ? (
            <ErrorState title="No se pudieron cargar las reglas" message={getApiErrorMessage(rulesQuery.error)} onRetry={() => rulesQuery.refetch()} />
          ) : null}

          <RewardApplicationsTable
            applications={filteredApplications}
            loading={applicationsQuery.isLoading}
            error={applicationsQuery.error}
            onRetry={() => applicationsQuery.refetch()}
            ruleMap={ruleMap}
          />
        </div>
      )}
    </Card>
  );
}
