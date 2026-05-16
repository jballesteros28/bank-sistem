import { useBranding } from "../api";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Badge } from "../../../shared/components/ui/Badge";

export function BrandingPage() {
  const brandingQuery = useBranding();
  const branding = brandingQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Branding de organizacion</h1>
        <p className="mt-1 text-sm text-slate-500">Preparado para editar marca, colores, dominio y white-label.</p>
      </div>
      {brandingQuery.isError ? <ErrorState message="No pudimos obtener el branding actual." onRetry={() => brandingQuery.refetch()} /> : null}
      <Card>
        <CardHeader title="Identidad actual" description="Valores leidos desde /organizaciones/me/branding cuando hay sesion activa." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">Nombre comercial</p>
            <p className="mt-1 text-sm font-semibold text-slate-950">{branding?.nombre_comercial || branding?.nombre || "-"}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">Moneda</p>
            <p className="mt-1 text-sm font-semibold text-slate-950">{branding?.moneda_default || "-"}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">Color primario</p>
            <Badge>{branding?.color_primario || "Default"}</Badge>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">White-label</p>
            <Badge tone={branding?.permite_white_label_activo ? "success" : "neutral"}>{branding?.permite_white_label_activo ? "Activo" : "Inactivo"}</Badge>
          </div>
        </div>
      </Card>
    </div>
  );
}
