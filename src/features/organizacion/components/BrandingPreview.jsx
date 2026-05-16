import { WalletCards } from "lucide-react";

import { formatCurrency } from "../../../shared/utils/formatters";

export function BrandingPreview({ branding = {} }) {
  const primary = branding.color_primario || "#0f766e";
  const secondary = branding.color_secundario || "#2563eb";
  const name = branding.nombre_comercial || branding.nombre || "Wallet SaaS";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-base font-semibold text-slate-950">Preview</h2>
        <p className="mt-1 text-sm text-slate-500">Vista rapida de marca aplicada a controles reales.</p>
      </div>
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          {branding.logo_url ? (
            <img className="h-11 w-11 rounded-md object-cover ring-1 ring-slate-200" src={branding.logo_url} alt="" />
          ) : (
            <div className="flex h-11 w-11 items-center justify-center rounded-md text-white" style={{ backgroundColor: primary }}>
              <WalletCards className="h-5 w-5" aria-hidden="true" />
            </div>
          )}
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-950">{name}</p>
            <p className="text-xs text-slate-500">{branding.subdominio ? `${branding.subdominio}.wallet.test` : "Operacion multi-tenant"}</p>
          </div>
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">Wallet empresa</p>
              <p className="mt-1 text-xs text-slate-500">{branding.moneda_default || "ARS"} - activa</p>
            </div>
            <span
              className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium text-white"
              style={{ backgroundColor: secondary }}
            >
              Principal
            </span>
          </div>
          <p className="mt-4 text-2xl font-semibold text-slate-950">{formatCurrency(25000, branding.moneda_default || "ARS")}</p>
          <button
            type="button"
            className="mt-5 h-10 rounded-md px-4 text-sm font-medium text-white shadow-sm"
            style={{ backgroundColor: primary }}
          >
            Accion primaria
          </button>
        </div>
      </div>
    </div>
  );
}
