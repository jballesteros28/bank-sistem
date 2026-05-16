import { humanizeRole } from "../../../shared/utils/formatters";

export function DashboardHeader({ user, branding }) {
  const organizationName = branding?.nombre_comercial || branding?.nombre || "Wallet SaaS";

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Hola, {user?.nombre || "usuario"}</h1>
        <p className="mt-1 text-sm text-slate-500">Resumen operativo de tu organizacion</p>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <p className="text-xs font-medium uppercase text-slate-400">Organizacion</p>
        <p className="mt-1 text-sm font-semibold text-slate-950">{organizationName}</p>
        <p className="mt-1 text-xs text-slate-500">{humanizeRole(user?.rol)}</p>
      </div>
    </div>
  );
}
