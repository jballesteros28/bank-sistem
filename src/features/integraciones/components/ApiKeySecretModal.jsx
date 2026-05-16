import { useState } from "react";
import { AlertTriangle, Check, Clipboard } from "lucide-react";

import { Button } from "../../../shared/components/ui/Button";
import { Modal } from "../../../shared/components/ui/Modal";

export function ApiKeySecretModal({ open, apiKey, keyPrefix, onClose }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  const handleCopy = async () => {
    if (!apiKey) {
      return;
    }

    if (!navigator.clipboard?.writeText) {
      setCopyError("El navegador bloqueo el portapapeles.");
      return;
    }

    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setCopyError("");
    } catch {
      setCopyError("No pudimos copiar la key automaticamente.");
    }
  };

  const handleClose = () => {
    setCopied(false);
    setCopyError("");
    onClose?.();
  };

  return (
    <Modal
      open={open}
      title="API Key creada"
      onClose={handleClose}
      footer={
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={handleClose}>
            Cerrar
          </Button>
          <Button icon={copied ? Check : Clipboard} onClick={handleCopy}>
            {copied ? "Copiada" : "Copiar key"}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold text-amber-900">Guardá esta key ahora. No volverá a mostrarse.</p>
              <p className="mt-1 text-sm text-amber-800">Las API Keys solo se muestran una vez al crearlas.</p>
            </div>
          </div>
        </div>
        {keyPrefix ? (
          <div>
            <p className="text-xs font-medium uppercase text-slate-400">Prefix visible</p>
            <p className="mt-1 font-mono text-sm text-slate-700">{keyPrefix}</p>
          </div>
        ) : null}
        <div>
          <p className="text-sm font-medium text-slate-700">Key real</p>
          <code className="mt-2 block break-all rounded-md border border-slate-200 bg-slate-50 p-3 font-mono text-sm text-slate-900">
            {apiKey}
          </code>
        </div>
        {copyError ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{copyError}</p> : null}
      </div>
    </Modal>
  );
}
