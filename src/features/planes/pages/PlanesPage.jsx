import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function PlanesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Plan actual y limites</h1>
        <p className="mt-1 text-sm text-slate-500">Consulta capacidades, limites mensuales y habilitaciones SaaS.</p>
      </div>
      <Card>
        <CardHeader title="Plan de la organizacion" description="Preparado para consumir /planes/organizacion/actual y mostrar uso contra limites." />
        <EmptyState title="Plan pendiente de cargar" description="El detalle del plan aparecera aqui cuando conectemos la vista completa." />
      </Card>
    </div>
  );
}
