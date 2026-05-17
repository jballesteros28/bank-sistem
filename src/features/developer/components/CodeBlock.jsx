import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "../../../shared/components/ui/Button";

function copyWithFallback(value) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(value);
  }

  const textArea = document.createElement("textarea");
  textArea.value = value;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "absolute";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(textArea);
  if (!copied) {
    throw new Error("Clipboard unavailable");
  }
  return Promise.resolve();
}

export function CodeBlock({ code, language = "bash", label = "Ejemplo" }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  const handleCopy = async () => {
    try {
      await copyWithFallback(code);
      setCopied(true);
      setCopyError("");
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
      setCopyError("No se pudo copiar desde este navegador.");
    }
  };

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-950">
      <div className="flex min-h-11 items-center justify-between gap-3 border-b border-slate-800 px-4 py-2">
        <p className="text-xs font-semibold uppercase tracking-normal text-slate-300">{label}</p>
        <Button
          variant="ghost"
          size="sm"
          icon={copied ? Check : Copy}
          className="bg-slate-900 text-slate-100 hover:bg-slate-800 hover:text-white"
          onClick={handleCopy}
        >
          {copied ? "Copiado" : "Copiar"}
        </Button>
      </div>
      <pre className="max-h-96 overflow-auto p-4 text-sm leading-6 text-slate-100">
        <code className={`language-${language}`}>{code}</code>
      </pre>
      {copyError ? <p className="border-t border-slate-800 px-4 py-2 text-xs text-amber-200">{copyError}</p> : null}
    </div>
  );
}
