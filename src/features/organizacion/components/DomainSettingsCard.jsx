import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { Input } from "../../../shared/components/ui/Input";
import { WhiteLabelNotice } from "./WhiteLabelNotice";

export function DomainSettingsCard({
  register,
  errors,
  disabled = false,
  whiteLabelAllowed = false,
  whiteLabelDisabled = false,
}) {
  return (
    <Card>
      <CardHeader title="White-label" description="Dominio, subdominio y activacion visual avanzada." />
      <div className="space-y-4">
        <WhiteLabelNotice allowed={whiteLabelAllowed} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Subdominio"
            error={errors.subdominio?.message}
            hint="ejemplo: mi-comercio"
            disabled={disabled}
            {...register("subdominio")}
          />
          <Input
            label="Dominio personalizado"
            error={errors.dominio_personalizado?.message}
            hint="ejemplo: app.midominio.com"
            disabled={disabled || whiteLabelDisabled}
            {...register("dominio_personalizado")}
          />
        </div>
        <label className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
          <input
            className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary disabled:cursor-not-allowed disabled:opacity-60"
            type="checkbox"
            disabled={disabled || whiteLabelDisabled}
            {...register("permite_white_label_activo")}
          />
          <span>
            <span className="block font-medium text-slate-800">Activar white-label avanzado</span>
            <span className="mt-0.5 block text-slate-500">Usa dominio personalizado cuando el plan lo permite.</span>
          </span>
        </label>
      </div>
    </Card>
  );
}
