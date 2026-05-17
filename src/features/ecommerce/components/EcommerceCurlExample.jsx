import { ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardHeader } from "../../../shared/components/ui/Card";

const orderPaidCurl = [
  "curl -X POST http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid \\",
  '  -H "X-API-Key: wsk_test_xxxxx" \\',
  '  -H "Content-Type: application/json" \\',
  "  -d '{",
  '    "proveedor": "generic",',
  '    "external_order_id": "order-1001",',
  '    "customer_email": "cliente@demo.com",',
  '    "customer_name": "Cliente Demo",',
  '    "amount": 20000,',
  '    "currency": "ARS",',
  '    "metadata": {',
  '      "source": "tienda-demo"',
  "    }",
  "  }'",
].join("\n");

export function EcommerceCurlExample({ canManage = false }) {
  return (
    <Card>
      <CardHeader
        title="Ejemplo de integracion curl"
        description="Simula una compra pagada contra el backend local de sandbox; en produccion reemplaza host y API Key."
        action={
          canManage ? (
            <Link
              to="/integraciones"
              className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-white px-3 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-slate-200 transition hover:bg-slate-50"
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              API Keys
            </Link>
          ) : null
        }
      />
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-950">
        <pre className="max-h-96 overflow-auto p-4 text-sm leading-6 text-slate-100">
          <code>{orderPaidCurl}</code>
        </pre>
      </div>
      <div className="mt-4 rounded-md border border-sky-200 bg-sky-50 px-4 py-3 text-sm leading-6 text-sky-900">
        Requiere API Key con scope <code className="rounded bg-white px-1.5 py-0.5 text-xs font-semibold">ecommerce:write</code>.
        No procesa dinero real; solo registra una compra pagada y aplica recompensa interna cuando corresponde.
        {!canManage ? <span className="block font-medium">Tu rol puede auditar las ordenes, pero no gestionar API Keys.</span> : null}
      </div>
    </Card>
  );
}
