import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Bell, LogOut, Menu } from "lucide-react";

import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { getUnreadNotificationsCount, notificationQueryKeys } from "../../../features/notificaciones/api";
import { useAuth } from "../../hooks/useAuth";
import { APP_NAME, ROUTES } from "../../utils/constants";
import { humanizeRole } from "../../utils/formatters";

export function Topbar({ branding }) {
  const { token, user, logout } = useAuth();
  const appName = branding?.nombre_comercial || APP_NAME;
  const unreadQuery = useQuery({
    queryKey: notificationQueryKeys.unreadCount,
    queryFn: getUnreadNotificationsCount,
    enabled: Boolean(token),
    retry: false,
  });
  const unreadCount = unreadQuery.isError ? 0 : unreadQuery.data || 0;
  const unreadLabel = unreadCount > 99 ? "99+" : String(unreadCount);

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
        <Link
          className="relative inline-flex h-9 w-9 items-center justify-center rounded-md bg-white text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 hover:text-brand-primary"
          to={ROUTES.notificaciones}
          aria-label="Ver notificaciones"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          {unreadCount > 0 ? (
            <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-rose-600 px-1.5 py-0.5 text-center text-[10px] font-semibold leading-none text-white">
              {unreadLabel}
            </span>
          ) : null}
        </Link>
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
