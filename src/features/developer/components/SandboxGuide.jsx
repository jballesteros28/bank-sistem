import { Badge } from "../../../shared/components/ui/Badge";
import { Card, CardHeader } from "../../../shared/components/ui/Card";

const demoUsers = [
  { role: "Super admin", email: "superadmin@demo.com" },
  { role: "Owner", email: "owner@demo.com" },
  { role: "Admin", email: "admin@demo.com" },
  { role: "Soporte", email: "soporte@demo.com" },
  { role: "Cliente", email: "cliente@demo.com" },
];

export function SandboxGuide() {
  return (
    <Card>
      <CardHeader
        title="Sandbox local"
        description="El seed de desarrollo deja usuarios, wallets, movimientos, API Key demo inactiva y webhook demo inactivo."
        action={<Badge tone="warning">solo desarrollo</Badge>}
      />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {demoUsers.map((user) => (
          <div key={user.email} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">{user.role}</p>
            <p className="mt-2 break-all text-sm font-semibold text-slate-950">{user.email}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">
        Password local: <code className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-900">Password123!</code>.
        Ejecuta <code className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-900">python scripts/dev_seed.py</code> para
        regenerar los datos demo sin duplicarlos.
      </p>
    </Card>
  );
}
