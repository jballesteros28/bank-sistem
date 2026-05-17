import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { CodeBlock } from "./CodeBlock";

const examples = [
  {
    label: "Crear deposito externo",
    code: [
      "curl -X POST http://127.0.0.1:8000/api/v1/ext/movimientos/deposito \\",
      '  -H "X-API-Key: wsk_test_xxxxx" \\',
      '  -H "Content-Type: application/json" \\',
      '  -d \'{ "wallet_destino_id": "...", "monto": 1000, "descripcion": "Carga externa" }\'',
    ].join("\n"),
  },
  {
    label: "Crear cashback",
    code: [
      "curl -X POST http://127.0.0.1:8000/api/v1/ext/movimientos/cashback \\",
      '  -H "X-API-Key: wsk_test_xxxxx" \\',
      '  -H "Content-Type: application/json" \\',
      '  -d \'{ "wallet_destino_id": "...", "monto": 250, "descripcion": "Cashback compra" }\'',
    ].join("\n"),
  },
  {
    label: "Compra ecommerce pagada",
    code: [
      "curl -X POST http://127.0.0.1:8000/api/v1/ext/ecommerce/order-paid \\",
      '  -H "X-API-Key: wsk_test_xxxxx" \\',
      '  -H "Content-Type: application/json" \\',
      '  -d \'{ "proveedor": "generic", "external_order_id": "order-1001", "customer_email": "cliente@demo.com", "amount": 20000, "currency": "ARS" }\'',
    ].join("\n"),
  },
  {
    label: "Listar movimientos",
    code: ['curl -X GET http://127.0.0.1:8000/api/v1/ext/movimientos \\', '  -H "X-API-Key: wsk_test_xxxxx"'].join(
      "\n",
    ),
  },
  {
    label: "Consultar wallet",
    code: ['curl -X GET http://127.0.0.1:8000/api/v1/ext/wallets/{wallet_id} \\', '  -H "X-API-Key: wsk_test_xxxxx"'].join(
      "\n",
    ),
  },
];

export function CurlExamples() {
  return (
    <Card>
      <CardHeader
        title="Endpoints externos"
        description="Ejemplos base para probar contra el backend local. Reemplaza la API Key y los IDs por datos de tu entorno."
      />
      <div className="grid gap-4 xl:grid-cols-2">
        {examples.map((example) => (
          <CodeBlock key={example.label} code={example.code} label={example.label} />
        ))}
      </div>
    </Card>
  );
}
