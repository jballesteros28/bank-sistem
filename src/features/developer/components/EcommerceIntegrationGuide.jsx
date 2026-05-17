import { ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { CodeBlock } from "./CodeBlock";

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
  '    "metadata": { "source": "tienda-demo" }',
  "  }'",
].join("\n");

export function EcommerceIntegrationGuide() {
  return (
    <Card>
      <CardHeader
        title="Ecommerce Integration"
        description="El ecommerce informa una compra pagada y Wallet SaaS aplica recompensa interna si hay una regla vigente."
        action={
          <Link
            to="/ecommerce"
            className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-white px-3 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-slate-200 transition hover:bg-slate-50"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            Ver ordenes
          </Link>
        }
      />
      <CodeBlock code={orderPaidCurl} label="Order paid" />
      <p className="mt-4 text-sm leading-6 text-slate-600">
        El endpoint requiere
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">
          ecommerce:write
        </code>
        . Usa
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">
          ecommerce:read
        </code>
        para consulta interna. La deduplicacion usa proveedor, organizacion y external_order_id. Los eventos disponibles son
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">
          ecommerce.order_paid
        </code>
        ,
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">
          ecommerce.order_processed
        </code>
        y
        <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-900">
          ecommerce.order_failed
        </code>
        .
      </p>
    </Card>
  );
}
