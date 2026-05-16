import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { getApiKeys, integrationsQueryKeys, revokeApiKey } from "../api";
import { ApiKeyCreateModal } from "./ApiKeyCreateModal";
import { ApiKeySecretModal } from "./ApiKeySecretModal";
import { ApiKeysTable } from "./ApiKeysTable";

export function ApiKeysPanel({ user, canManage = false, canView = true }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [createdApiKey, setCreatedApiKey] = useState(null);
  const organizationId = user?.organizacion_id || "current";

  const apiKeysQuery = useQuery({
    queryKey: integrationsQueryKeys.apiKeys(organizationId),
    queryFn: () => getApiKeys(),
    enabled: canView,
    retry: false,
  });

  const revokeMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsQueryKeys.all });
      showToast({
        title: "API Key revocada",
        message: "La key dejo de autenticar solicitudes externas.",
      });
    },
    onError: (error) => {
      showToast({
        title: "No se pudo revocar",
        message: getApiErrorMessage(error),
      });
    },
  });

  const handleCreated = (apiKey) => {
    setCreateOpen(false);
    setCreatedApiKey(apiKey);
  };

  return (
    <>
      <Card>
        <CardHeader
          title="API Keys"
          description="Credenciales externas con scopes acotados por organizacion."
          action={
            canManage ? (
              <Button icon={Plus} onClick={() => setCreateOpen(true)}>
                Crear API Key
              </Button>
            ) : null
          }
        />
        <ApiKeysTable
          apiKeys={apiKeysQuery.data || []}
          loading={apiKeysQuery.isLoading}
          error={apiKeysQuery.error}
          onRetry={() => apiKeysQuery.refetch()}
          canManage={canManage}
          onRevoke={(apiKey) => revokeMutation.mutate(apiKey.id)}
          revokingId={revokeMutation.isPending ? revokeMutation.variables : null}
        />
      </Card>
      <ApiKeyCreateModal open={createOpen} onClose={() => setCreateOpen(false)} onCreated={handleCreated} />
      <ApiKeySecretModal
        open={Boolean(createdApiKey?.api_key)}
        apiKey={createdApiKey?.api_key}
        keyPrefix={createdApiKey?.key_prefix}
        onClose={() => setCreatedApiKey(null)}
      />
    </>
  );
}
