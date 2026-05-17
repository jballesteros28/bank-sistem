import { Calculator, Gift, ListChecks, TableProperties } from "lucide-react";

const baseTabs = [
  { id: "reglas", label: "Reglas", icon: ListChecks },
  { id: "simulador", label: "Simulador", icon: Calculator },
  { id: "aplicar", label: "Aplicar recompensa", icon: Gift, requiresApply: true },
  { id: "aplicaciones", label: "Aplicaciones", icon: TableProperties },
];

export function RewardsTabs({ activeTab, onChange, canApply = false }) {
  const tabs = baseTabs.filter((tab) => !tab.requiresApply || canApply);

  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Secciones de recompensas">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const active = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            className={[
              "inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm font-medium ring-1 transition",
              active ? "bg-brand-primary text-white ring-brand-primary" : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50",
            ].join(" ")}
            onClick={() => onChange(tab.id)}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
