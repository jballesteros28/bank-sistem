import { LogOut, Menu } from "lucide-react";

import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { useAuth } from "../../hooks/useAuth";
import { APP_NAME } from "../../utils/constants";
import { humanizeRole } from "../../utils/formatters";

export function Topbar({ branding }) {
  const { user, logout } = useAuth();
  const appName = branding?.nombre_comercial || APP_NAME;

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Button variant="ghost" size="sm" icon={Menu} className="lg:hidden" aria-label="Abrir menu">
          Menu
        </Button>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-950">{appName}</p>
          <p className="hidden text-xs text-slate-500 sm:block">Operacion multi-tenant</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {user ? (
          <div className="hidden items-center gap-2 sm:flex">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-950">{user.nombre}</p>
              <p className="text-xs text-slate-500">{user.email}</p>
            </div>
            <Badge tone="info">{humanizeRole(user.rol)}</Badge>
          </div>
        ) : null}
        <Button variant="secondary" size="sm" icon={LogOut} onClick={() => logout()}>
          Salir
        </Button>
      </div>
    </header>
  );
}
