import { CheckCircle2, XCircle } from "lucide-react";

function Feature({ enabled, label }) {
  const Icon = enabled ? CheckCircle2 : XCircle;

  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className={["h-4 w-4", enabled ? "text-emerald-600" : "text-slate-300"].join(" ")} aria-hidden="true" />
      <span className={enabled ? "text-slate-800" : "text-slate-500"}>{label}</span>
    </div>
  );
}

export function PlanFeatureList({ plan }) {
  return (
    <div className="space-y-2">
      <Feature enabled={plan?.permite_webhooks} label="Webhooks" />
      <Feature enabled={plan?.permite_white_label} label="White-label" />
    </div>
  );
}
