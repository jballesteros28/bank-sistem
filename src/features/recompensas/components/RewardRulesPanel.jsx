import { useQuery } from "@tanstack/react-query";
import { Gift, Plus } from "lucide-react";
import { useState } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { getRewardRules, rewardQueryKeys } from "../api";
import { RewardRuleCard } from "./RewardRuleCard";
import { RewardRuleModal } from "./RewardRuleModal";

function RulesSkeleton() {
  return (
    <div className="grid gap-4">
      {[0, 1, 2].map((item) => (
        <div key={item} className="h-44 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

export function RewardRulesPanel({ user, canManage = false, canView = true }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);
  const organizationId = user?.organizacion_id || "global";

  const rulesQuery = useQuery({
    queryKey: rewardQueryKeys.rewardRules(organizationId),
    queryFn: () => getRewardRules(),
    enabled: canView,
    retry: false,
  });

  const openCreate = () => {
    setSelectedRule(null);
    setModalOpen(true);
  };

  const openEdit = (rule) => {
    setSelectedRule(rule);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedRule(null);
  };

  const rules = rulesQuery.data || [];

  return (
    <>
      <Card>
        <CardHeader
          title="Reglas de recompensa"
          description="Cashback, puntos y credito interno configurados para la organizacion."
          action={
            canManage ? (
              <Button icon={Plus} onClick={openCreate}>
                Crear regla
              </Button>
            ) : null
          }
        />

        {!canView ? (
          <EmptyState icon={Gift} title="Sin permisos" description="Tu rol no puede consultar reglas de recompensa." />
        ) : rulesQuery.isLoading ? (
          <RulesSkeleton />
        ) : rulesQuery.error ? (
          <ErrorState title="No se pudieron cargar las reglas" message={getApiErrorMessage(rulesQuery.error)} onRetry={() => rulesQuery.refetch()} />
        ) : !rules.length ? (
          <EmptyState
            icon={Gift}
            title="Sin reglas"
            description="Todavia no hay reglas de cashback, puntos o credito interno."
            action={
              canManage ? (
                <Button icon={Plus} onClick={openCreate}>
                  Crear regla
                </Button>
              ) : null
            }
          />
        ) : (
          <div className="grid gap-4">
            {rules.map((rule) => (
              <RewardRuleCard key={rule.id} rule={rule} canManage={canManage} onEdit={openEdit} />
            ))}
          </div>
        )}
      </Card>

      <RewardRuleModal open={modalOpen} rule={selectedRule} onClose={closeModal} />
    </>
  );
}
