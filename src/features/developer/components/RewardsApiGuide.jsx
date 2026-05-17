import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { CodeBlock } from "./CodeBlock";

const rewardsExample = [
  "curl -X POST http://127.0.0.1:8000/api/v1/recompensas/simular \\",
  '  -H "Authorization: Bearer <jwt>" \\',
  '  -H "Content-Type: application/json" \\',
  '  -d \'{ "monto_compra": 20000, "tipo": "cashback" }\'',
].join("\n");

export function RewardsApiGuide() {
  return (
    <Card>
      <CardHeader
        title="Recompensas API"
        description="Reglas, simulacion, aplicacion manual y consultas de recompensas usan JWT de usuario por ahora."
      />
      <CodeBlock code={rewardsExample} label="Simular recompensa" />
      <p className="mt-4 text-sm leading-6 text-slate-600">
        La API externa de recompensas con API Key queda reservada para una fase futura. El evento disponible para webhooks es
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">recompensa.aplicada</code>.
      </p>
    </Card>
  );
}
