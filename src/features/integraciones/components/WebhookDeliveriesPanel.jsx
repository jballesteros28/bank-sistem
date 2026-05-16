import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { getWebhookDeliveries, integrationsQueryKeys, retryWebhookDelivery } from "../api";
import { WebhookDeliveriesTable } from "./WebhookDeliveriesTable";

export function WebhookDeliveriesPanel({ user, canView = true, canRetry = false }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [actionError, setActionError] = useState("");
  const organizationId = user?.organizacion_id || "current";
  const params = useMemo(() => ({ skip: 0, limit: 100 }), []);

  const deliveriesQuery = useQuery({
    queryKey: integrationsQueryKeys.deliveries(organizationId, params),
    queryFn: () => getWebhookDeliveries(params),
    enabled: canView,
    retry: false,
  });

  const retryMutation = useMutation({
    mutationFn: retryWebhookDelivery,
    onSuccess: () => {
      setActionError("");
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.deliveries(organizationId, params) });
      showToast({
        title: "Reenvio agendado",
        message: "El delivery quedo pendiente para un nuevo intento.",
      });
    },
    onError: (error) => {
      setActionError(getApiErrorMessage(error));
    },
  });

  return (
    <Card>
      <CardHeader
        title="Deliveries"
        description="Intentos de envio de webhooks y reintentos manuales."
        action={
          <Button variant="secondary" icon={RefreshCw} onClick={() => deliveriesQuery.refetch()} loading={deliveriesQuery.isFetching}>
            Actualizar
          </Button>
        }
      />
      {actionError ? <ErrorState title="No se pudo reenviar" message={actionError} /> : null}
      <WebhookDeliveriesTable
        deliveries={deliveriesQuery.data || []}
        loading={deliveriesQuery.isLoading}
        error={deliveriesQuery.error}
        onRetryQuery={() => deliveriesQuery.refetch()}
        onRetryDelivery={(delivery) => retryMutation.mutate(delivery.id)}
        retryingId={retryMutation.isPending ? retryMutation.variables : null}
        canRetry={canRetry}
      />
    </Card>
  );
}
