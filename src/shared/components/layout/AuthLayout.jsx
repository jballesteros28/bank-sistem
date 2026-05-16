import { Outlet } from "react-router-dom";

import { APP_NAME } from "../../utils/constants";

export function AuthLayout() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="grid min-h-screen lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section className="hidden border-r border-slate-800 bg-slate-950 px-10 py-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-md bg-brand-primary" />
            <div>
              <p className="text-base font-semibold">{APP_NAME}</p>
              <p className="text-sm text-slate-400">Consola SaaS</p>
            </div>
          </div>
          <div className="max-w-md">
            <h1 className="text-3xl font-semibold tracking-normal">Wallet SaaS para operar organizaciones</h1>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Alta de tenants, owners, wallets e identidad visual desde una consola preparada para crecer por etapas.
            </p>
          </div>
          <p className="text-xs text-slate-500">API conectada en tiempo real contra el backend local.</p>
        </section>
        <section className="flex min-h-screen w-full items-center justify-center px-4 py-10">
          <Outlet />
        </section>
      </div>
    </main>
  );
}
