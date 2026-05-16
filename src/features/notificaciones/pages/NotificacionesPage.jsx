import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function NotificacionesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Notificaciones</h1>
        <p className="mt-1 text-sm text-slate-500">Centro de eventos internos y estados de lectura.</p>
      </div>
      <Card>
        <CardHeader title="Bandeja" description="Preparado para listar notificaciones internas y acciones de marcado como leida." />
        <EmptyState title="No hay notificaciones" description="Los eventos de wallets, movimientos y seguridad se mostraran aqui." />
      </Card>
    </div>
  );
}
