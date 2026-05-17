import { Link } from "react-router-dom";
import { Bell, CreditCard, ReceiptText } from "lucide-react";

import { Card, CardHeader } from "../../../../shared/components/ui/Card";
import { ROUTES } from "../../../../shared/utils/constants";
import { formatNumber } from "../../../../shared/utils/formatters";

export function ClientQuickActions({ unreadCount = 0, unreadLoading = false, onPay }) {
  const actions = [
    { label: "Pagar a organizacion", icon: CreditCard, onClick: onPay },
    { label: "Ver movimientos", icon: ReceiptText, to: ROUTES.movimientos },
    { label: "Ver notificaciones", icon: Bell, to: ROUTES.notificaciones },
  ];

  return (
    <Card>
      <CardHeader title="Acciones" description="Atajos para operar con tu wallet." />
      <div className="space-y-3">
        {actions.map((action) => {
          const content = (
            <>
              <action.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{action.label}</span>
            </>
          );

          if (action.to) {
            return (
              <Link
                key={action.label}
                className="flex min-h-12 items-center gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-brand-primary hover:text-brand-primary"
                to={action.to}
              >
                {content}
              </Link>
            );
          }

          return (
            <button
              key={action.label}
              type="button"
              className="flex min-h-12 w-full items-center gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm font-medium text-slate-700 transition hover:border-brand-primary hover:text-brand-primary"
              onClick={action.onClick}
            >
              {content}
            </button>
          );
        })}
      </div>
      <div className="mt-5 rounded-md bg-slate-50 px-3 py-3">
        <p className="text-xs font-medium uppercase text-slate-400">No leidas</p>
        {unreadLoading ? (
          <div className="mt-2 h-6 w-16 animate-pulse rounded bg-slate-100" />
        ) : (
          <p className="mt-1 text-2xl font-semibold text-slate-950">{formatNumber(unreadCount)}</p>
        )}
      </div>
    </Card>
  );
}
