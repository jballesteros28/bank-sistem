import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { CodeBlock } from "./CodeBlock";

const apiKeyHeader = "X-API-Key: wsk_test_xxxxx";

export function ApiKeyGuide() {
  return (
    <Card>
      <CardHeader
        title="Autenticacion con API Key"
        description="Los endpoints externos no usan JWT de usuarios. Cada request debe enviar una API Key activa de la organizacion."
      />
      <CodeBlock code={apiKeyHeader} language="http" label="Header requerido" />
      <p className="mt-4 text-sm leading-6 text-slate-600">
        La key real solo se muestra una vez al crearla desde Integraciones. Los listados conservan el prefijo para auditoria sin
        exponer el secreto completo.
      </p>
    </Card>
  );
}
