import { X } from "lucide-react";

import { Button } from "./Button";

export function Modal({ open, title, children, footer, onClose, panelClassName = "" }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4 py-6">
      <div
        className={[
          "flex max-h-[calc(100vh-3rem)] w-full max-w-lg flex-col overflow-hidden rounded-lg bg-white shadow-panel",
          panelClassName,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">{title}</h2>
          <Button variant="ghost" size="sm" icon={X} onClick={onClose} aria-label="Cerrar">
            Cerrar
          </Button>
        </div>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
        {footer ? <div className="shrink-0 border-t border-slate-200 px-5 py-4">{footer}</div> : null}
      </div>
    </div>
  );
}
