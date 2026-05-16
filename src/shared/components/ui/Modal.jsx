import { X } from "lucide-react";

import { Button } from "./Button";

export function Modal({ open, title, children, footer, onClose }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4 py-6">
      <div className="w-full max-w-lg rounded-lg bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">{title}</h2>
          <Button variant="ghost" size="sm" icon={X} onClick={onClose} aria-label="Cerrar">
            Cerrar
          </Button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {footer ? <div className="border-t border-slate-200 px-5 py-4">{footer}</div> : null}
      </div>
    </div>
  );
}
