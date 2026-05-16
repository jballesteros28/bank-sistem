import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function IntegracionesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">API Keys y Webhooks</h1>
        <p className="mt-1 text-sm text-slate-500">Administra acceso externo, eventos, deliveries y reintentos manuales.</p>
      </div>
      <Card>
        <CardHeader title="Integraciones" description="La fundacion queda lista para API Keys, Webhooks y deliveries con reenvio." />
        <EmptyState title="Sin integraciones visibles" description="Cuando conectemos formularios, se podran crear API Keys y endpoints webhook." />
      </Card>
    </div>
  );
}
