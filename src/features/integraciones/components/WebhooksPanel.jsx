import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Plus } from "lucide-react";
import { useState } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { deleteWebhook, getWebhooks, integrationsQueryKeys, updateWebhook } from "../api";
import { WebhookCreateModal } from "./WebhookCreateModal";
import { WebhooksTable } from "./WebhooksTable";

function PlanNotice({ loading, error, allowsWebhooks, canManageByRole }) {
  if (!canManageByRole) {
    return null;
  }

  if (loading) {
    return <div className="mb-4 rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">Confirmando plan actual.</div>;
  }

  if (error) {
    return (
      <ErrorState
        title="Plan actual no disponible"
        message="No pudimos confirmar si el plan permite webhooks. Las acciones quedan deshabilitadas."
      />
    );
  }

  if (!allowsWebhooks) {
    return (
      <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 p-4">
        <div className="flex gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
          <p className="text-sm font-semibold text-amber-900">Tu plan actual no incluye webhooks.</p>
        </div>
      </div>
    );
  }

  return null;
}

export function WebhooksPanel({
  user,
  canView = true,
  canManageByRole = false,
  planAllowsWebhooks = false,
  planLoading = false,
  planError,
}) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [actionError, setActionError] = useState("");
  const organizationId = user?.organizacion_id || "current";
  const actionsEnabled = canManageByRole && planAllowsWebhooks && !planLoading && !planError;

  const webhooksQuery = useQuery({
    queryKey: integrationsQueryKeys.webhooks(organizationId),
    queryFn: () => getWebhooks(),
    enabled: canView,
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: ({ webhookId, payload }) => updateWebhook(webhookId, payload),
    onSuccess: () => {
      setActionError("");
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.all });
      showToast({
        title: "Webhook actualizado",
        message: "El estado del webhook fue actualizado.",
      });
    },
    onError: (error) => {
      setActionError(getApiErrorMessage(error));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteWebhook,
    onSuccess: () => {
      setActionError("");
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.all });
      showToast({
        title: "Webhook desactivado",
        message: "El endpoint dejo de recibir eventos.",
      });
    },
    onError: (error) => {
      setActionError(getApiErrorMessage(error));
    },
  });

  const handleDelete = (webhook) => {
    const confirmed = window.confirm("Eliminar este webhook? El backend lo marcara como inactivo.");
    if (confirmed) {
      deleteMutation.mutate(webhook.id);
    }
  };

  return (
    <>
      <Card>
        <CardHeader
          title="Webhooks"
          description="Endpoints que reciben eventos firmados con HMAC."
          action={
            canManageByRole ? (
              <Button icon={Plus} disabled={!actionsEnabled} onClick={() => setCreateOpen(true)}>
                Crear webhook
              </Button>
            ) : null
          }
        />
        <PlanNotice loading={planLoading} error={planError} allowsWebhooks={planAllowsWebhooks} canManageByRole={canManageByRole} />
        {actionError ? <ErrorState title="No se pudo actualizar" message={actionError} /> : null}
        <WebhooksTable
          webhooks={webhooksQuery.data || []}
          loading={webhooksQuery.isLoading}
          error={webhooksQuery.error}
          onRetry={() => webhooksQuery.refetch()}
          canManage={actionsEnabled}
          onToggle={(webhook) => updateMutation.mutate({ webhookId: webhook.id, payload: { activo: !webhook.activo } })}
          onDelete={handleDelete}
          updatingId={updateMutation.isPending ? updateMutation.variables?.webhookId : null}
          deletingId={deleteMutation.isPending ? deleteMutation.variables : null}
        />
      </Card>
      <WebhookCreateModal open={createOpen} onClose={() => setCreateOpen(false)} onCreated={() => setCreateOpen(false)} />
    </>
  );
}
