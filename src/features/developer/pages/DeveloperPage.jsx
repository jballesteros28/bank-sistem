import { LockKeyhole } from "lucide-react";

import { ApiKeyGuide } from "../components/ApiKeyGuide";
import { CurlExamples } from "../components/CurlExamples";
import { DeveloperHero } from "../components/DeveloperHero";
import { SandboxGuide } from "../components/SandboxGuide";
import { ScopesGuide } from "../components/ScopesGuide";
import { WebhookSignatureGuide } from "../components/WebhookSignatureGuide";
import { WebhooksGuide } from "../components/WebhooksGuide";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canViewDeveloperPortal } from "../../../shared/utils/roles";

export function DeveloperPage() {
  const { user } = useAuth();
  const canView = canViewDeveloperPortal(user);

  if (!canView) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Developer Portal</h1>
          <p className="mt-1 text-sm text-slate-500">Documentacion tecnica para integraciones externas.</p>
        </div>
        <Card>
          <CardHeader title="Sin permisos" description="El portal developer esta disponible para roles administrativos y soporte." />
          <EmptyState
            icon={LockKeyhole}
            title="No tenes permisos para ver el Developer Portal."
            description="Tu rol actual no puede consultar documentacion tecnica de integraciones."
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DeveloperHero />
      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <ApiKeyGuide />
        <SandboxGuide />
      </div>
      <ScopesGuide />
      <CurlExamples />
      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <WebhooksGuide />
        <WebhookSignatureGuide />
      </div>
    </div>
  );
}
