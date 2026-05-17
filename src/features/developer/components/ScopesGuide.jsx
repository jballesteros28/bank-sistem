import { Table } from "../../../shared/components/ui/Table";
import { Card, CardHeader } from "../../../shared/components/ui/Card";

const scopes = [
  { scope: "wallets:read", description: "Consultar wallets desde endpoints externos." },
  { scope: "wallets:write", description: "Crear o modificar recursos de wallets permitidos por la API externa." },
  { scope: "movimientos:read", description: "Listar movimientos visibles para la organizacion de la API Key." },
  { scope: "movimientos:write", description: "Crear depositos y cashback desde sistemas externos." },
  { scope: "ecommerce:read", description: "Consultar eventos ecommerce recibidos." },
  { scope: "ecommerce:write", description: "Recibir compras pagadas desde una tienda externa." },
  { scope: "usuarios:read", description: "Consultar datos de usuarios cuando exista endpoint externo compatible." },
  { scope: "usuarios:write", description: "Administrar usuarios cuando exista endpoint externo compatible." },
  { scope: "webhooks:read", description: "Consultar configuracion y deliveries de webhooks cuando aplique." },
  { scope: "webhooks:write", description: "Administrar webhooks cuando el plan y rol lo permitan." },
];

const columns = [
  {
    key: "scope",
    header: "Scope",
    render: (row) => <code className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-900">{row.scope}</code>,
  },
  { key: "description", header: "Uso" },
];

export function ScopesGuide() {
  return (
    <Card>
      <CardHeader title="Scopes" description="Cada API Key declara permisos granulares. El backend valida el scope requerido por endpoint." />
      <Table columns={columns} rows={scopes} getRowKey={(row) => row.scope} />
    </Card>
  );
}
