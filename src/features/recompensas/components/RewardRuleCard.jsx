import { Pencil } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { formatCurrency, formatDate, formatLimit, formatNumber } from "../../../shared/utils/formatters";
import { RewardRuleStatusBadge } from "./RewardRuleStatusBadge";
import { RewardTypeBadge } from "./RewardTypeBadge";

function formatRewardValue(value, currency) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (currency === "PUNTOS") {
    return `${formatNumber(value)} PUNTOS`;
  }
  return formatCurrency(value, currency);
}

function formatRuleBenefit(rule) {
  const parts = [];
  if (rule.porcentaje_cashback !== null && rule.porcentaje_cashback !== undefined) {
    parts.push(`${formatNumber(rule.porcentaje_cashback)}%`);
  }
  if (rule.monto_fijo !== null && rule.monto_fijo !== undefined) {
    parts.push(formatRewardValue(rule.monto_fijo, rule.moneda_recompensa));
  }
  return parts.join(" + ") || "-";
}

function DetailItem({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-normal text-slate-400">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-800">{value}</dd>
    </div>
  );
}

export function RewardRuleCard({ rule, canManage = false, onEdit }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <RewardTypeBadge type={rule.tipo} />
            <RewardRuleStatusBadge status={rule.estado} />
          </div>
          <h3 className="mt-3 truncate text-base font-semibold text-slate-950">{rule.nombre}</h3>
          {rule.descripcion ? <p className="mt-1 line-clamp-2 text-sm text-slate-500">{rule.descripcion}</p> : null}
        </div>
        {canManage ? (
          <Button variant="secondary" size="sm" icon={Pencil} onClick={() => onEdit(rule)}>
            Editar
          </Button>
        ) : null}
      </div>

      <dl className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <DetailItem label="Beneficio" value={formatRuleBenefit(rule)} />
        <DetailItem label="Moneda" value={rule.moneda_recompensa || "-"} />
        <DetailItem
          label="Compra minima"
          value={rule.monto_minimo_compra === null || rule.monto_minimo_compra === undefined ? "Sin minimo" : formatNumber(rule.monto_minimo_compra)}
        />
        <DetailItem
          label="Tope"
          value={
            rule.monto_maximo_recompensa === null || rule.monto_maximo_recompensa === undefined
              ? formatLimit(null)
              : formatRewardValue(rule.monto_maximo_recompensa, rule.moneda_recompensa)
          }
        />
        <DetailItem label="Acumulable" value={rule.acumulable ? "Si" : "No"} />
        <DetailItem label="Inicio" value={formatDate(rule.fecha_inicio)} />
        <DetailItem label="Fin" value={formatDate(rule.fecha_fin)} />
        <DetailItem label="ID" value={<span className="font-mono text-xs text-slate-500">{rule.id}</span>} />
      </dl>
    </article>
  );
}
