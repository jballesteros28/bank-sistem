import { AlertCircle, CheckCircle2 } from "lucide-react";

export function WhiteLabelNotice({ allowed }) {
  const Icon = allowed ? CheckCircle2 : AlertCircle;

  return (
    <div className={[
      "rounded-lg border p-4",
      allowed ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50",
    ].join(" ")}>
      <div className="flex gap-3">
        <Icon className={[
          "mt-0.5 h-5 w-5 shrink-0",
          allowed ? "text-emerald-600" : "text-amber-600",
        ].join(" ")} aria-hidden="true" />
        <div>
          <p className={["text-sm font-semibold", allowed ? "text-emerald-900" : "text-amber-900"].join(" ")}>
            {allowed ? "White-label avanzado disponible" : "Tu plan actual no incluye white-label avanzado."}
          </p>
          <p className={["mt-1 text-sm", allowed ? "text-emerald-700" : "text-amber-700"].join(" ")}>
            {allowed
              ? "Podes activar dominio personalizado y white-label avanzado."
              : "El subdominio puede configurarse, pero dominio personalizado y activacion avanzada quedan bloqueados."}
          </p>
        </div>
      </div>
    </div>
  );
}
