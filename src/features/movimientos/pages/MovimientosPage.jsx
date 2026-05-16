import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function MovimientosPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Movimientos</h1>
        <p className="mt-1 text-sm text-slate-500">Seguimiento de depositos, pagos, transferencias, cashback y reversas.</p>
      </div>
      <Card>
        <CardHeader title="Actividad reciente" description="La vista esta lista para incorporar tabla, filtros por fecha y detalle de movimiento." />
        <EmptyState title="Sin movimientos visibles" description="Los movimientos aprobados apareceran aqui respetando permisos por rol." />
      </Card>
    </div>
  );
}
