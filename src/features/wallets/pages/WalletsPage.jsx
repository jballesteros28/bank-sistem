import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function WalletsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Wallets</h1>
        <p className="mt-1 text-sm text-slate-500">Consulta wallets de usuarios y de la organizacion.</p>
      </div>
      <Card>
        <CardHeader title="Listado de wallets" description="La integracion con filtros y acciones queda preparada sobre el modulo de wallets." />
        <EmptyState title="Sin wallets cargadas" description="Cuando conectemos la grilla, veras balances, estado y owner de cada wallet." />
      </Card>
    </div>
  );
}
