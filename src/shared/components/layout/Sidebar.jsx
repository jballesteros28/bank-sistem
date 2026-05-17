import { NavLink } from "react-router-dom";
import { Bell, Code2, CreditCard, Home, KeyRound, Layers3, Palette, ReceiptText, UsersRound } from "lucide-react";

import { APP_NAME, ROUTES } from "../../utils/constants";
import { canViewDeveloperPortal, canViewUsers } from "../../utils/roles";
import { useAuth } from "../../hooks/useAuth";

const navItems = [
  { label: "Dashboard", to: ROUTES.dashboard, icon: Home },
  { label: "Wallets", to: ROUTES.wallets, icon: CreditCard },
  { label: "Movimientos", to: ROUTES.movimientos, icon: ReceiptText },
  { label: "Notificaciones", to: ROUTES.notificaciones, icon: Bell },
  { label: "Branding", to: ROUTES.branding, icon: Palette },
  { label: "Planes", to: ROUTES.planes, icon: Layers3 },
  { label: "Integraciones", to: ROUTES.integraciones, icon: KeyRound },
  { label: "Developer", to: ROUTES.developer, icon: Code2, canView: canViewDeveloperPortal },
  { label: "Usuarios", to: ROUTES.usuarios, icon: UsersRound, canView: canViewUsers },
];

export function Sidebar({ branding }) {
  const { user } = useAuth();
  const appName = branding?.nombre_comercial || APP_NAME;

  return (
    <aside className="hidden w-72 shrink-0 border-r border-slate-200 bg-white lg:block">
      <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
        {branding?.logo_url ? <img src={branding.logo_url} alt={appName} className="h-8 w-8 rounded-md object-contain" /> : <div className="h-8 w-8 rounded-md bg-brand-primary" />}
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-950">{appName}</p>
          <p className="text-xs text-slate-500">Consola SaaS</p>
        </div>
      </div>
      <nav className="space-y-1 px-3 py-4">
        {navItems.map((item) => {
          if (item.canView && !item.canView(user)) {
            return null;
          }

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition",
                  isActive ? "bg-brand-primary text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
                ].join(" ")
              }
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
