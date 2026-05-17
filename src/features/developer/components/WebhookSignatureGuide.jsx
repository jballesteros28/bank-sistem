import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { CodeBlock } from "./CodeBlock";

const headers = [
  { name: "X-Wallet-Signature", detail: "Firma HMAC SHA256 con formato sha256=<hex>." },
  { name: "X-Wallet-Event", detail: "Nombre del evento enviado." },
  { name: "X-Wallet-Delivery-Id", detail: "ID del delivery para auditoria y reintentos." },
];

const hmacExample = [
  'const crypto = require("crypto");',
  "",
  "function verifySignature(payload, signature, secret) {",
  "  const expected = crypto",
  '    .createHmac("sha256", secret)',
  "    .update(payload)",
  '    .digest("hex");',
  "",
  '  return "sha256=" + expected === signature;',
  "}",
].join("\n");

export function WebhookSignatureGuide() {
  return (
    <Card>
      <CardHeader
        title="Firma HMAC"
        description="Cada delivery incluye headers para identificar el evento y validar que el payload no fue alterado."
      />
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        {headers.map((header) => (
          <div key={header.name} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <code className="text-xs font-semibold text-slate-950">{header.name}</code>
            <p className="mt-2 text-sm leading-5 text-slate-600">{header.detail}</p>
          </div>
        ))}
      </div>
      <CodeBlock code={hmacExample} language="javascript" label="Verificacion JavaScript" />
    </Card>
  );
}
