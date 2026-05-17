import { LockKeyhole } from "lucide-react";
import { useState } from "react";

import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import {
  canApplyRewards,
  canManageRewardRules,
  canSimulateRewards,
  canViewRewardApplications,
  canViewRewards,
  isClient,
} from "../../../shared/utils/roles";
import { ApplyRewardPanel } from "../components/ApplyRewardPanel";
import { ClientRewardsPanel } from "../components/ClientRewardsPanel";
import { RewardApplicationsPanel } from "../components/RewardApplicationsPanel";
import { RewardRulesPanel } from "../components/RewardRulesPanel";
import { RewardSimulatorPanel } from "../components/RewardSimulatorPanel";
import { RewardsTabs } from "../components/RewardsTabs";

function renderAdminTab(activeTab, user, permissions) {
  if (activeTab === "simulador") {
    return <RewardSimulatorPanel user={user} canSimulate={permissions.canSimulate} />;
  }
  if (activeTab === "aplicar") {
    return <ApplyRewardPanel user={user} canApply={permissions.canApply} />;
  }
  if (activeTab === "aplicaciones") {
    return <RewardApplicationsPanel user={user} canView={permissions.canViewApplications} />;
  }
  return <RewardRulesPanel user={user} canView={permissions.canView} canManage={permissions.canManageRules} />;
}

export function RecompensasPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("reglas");

  const permissions = {
    canView: canViewRewards(user),
    canManageRules: canManageRewardRules(user),
    canApply: canApplyRewards(user),
    canSimulate: canSimulateRewards(user),
    canViewApplications: canViewRewardApplications(user),
  };

  const visibleActiveTab = activeTab === "aplicar" && !permissions.canApply ? "reglas" : activeTab;

  if (!permissions.canView) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Recompensas</h1>
          <p className="mt-1 text-sm text-slate-500">Cashback, puntos y credito interno.</p>
        </div>
        <Card>
          <CardHeader title="Sin permisos" description="Tu rol actual no puede acceder a recompensas." />
          <EmptyState icon={LockKeyhole} title="No tenes permisos" description="La seguridad real la mantiene el backend para cada endpoint." />
        </Card>
      </div>
    );
  }

  if (isClient(user)) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Recompensas</h1>
          <p className="mt-1 text-sm text-slate-500">Tus beneficios acreditados por compras y promociones.</p>
        </div>
        <ClientRewardsPanel user={user} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Recompensas</h1>
        <p className="mt-1 text-sm text-slate-500">
          Administra reglas de cashback, puntos y credito interno para la organizacion.
        </p>
      </div>

      <RewardsTabs activeTab={visibleActiveTab} onChange={setActiveTab} canApply={permissions.canApply} />
      {renderAdminTab(visibleActiveTab, user, permissions)}
    </div>
  );
}
