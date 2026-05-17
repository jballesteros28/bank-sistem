import { KeyRound, RadioTower, ShieldCheck } from "lucide-react";

const highlights = [
  {
    icon: KeyRound,
    title: "API externa",
    description: "Endpoints protegidos con el header X-API-Key para sistemas externos.",
  },
  {
    icon: RadioTower,
    title: "Webhooks",
    description: "Eventos operativos firmados para sincronizar wallets, movimientos y pagos.",
  },
  {
    icon: ShieldCheck,
    title: "HMAC",
    description: "Cada delivery puede verificarse con el secret configurado por la organizacion.",
  },
];

export function DeveloperHero() {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-normal text-brand-primary">Developer Portal</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-slate-950">Integraciones para Wallet SaaS</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Wallet SaaS funciona como infraestructura para operar wallets internas, movimientos y eventos de negocio. Este portal
          resume la autenticacion con API Key, scopes disponibles, webhooks firmados y ejemplos para sandbox local.
        </p>
      </div>
      <div className="mt-6 grid gap-3 md:grid-cols-3">
        {highlights.map((item) => (
          <div key={item.title} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white text-brand-primary ring-1 ring-slate-200">
              <item.icon className="h-4 w-4" aria-hidden="true" />
            </div>
            <h2 className="mt-3 text-sm font-semibold text-slate-950">{item.title}</h2>
            <p className="mt-1 text-sm leading-5 text-slate-600">{item.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
