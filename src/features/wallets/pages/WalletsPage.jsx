import { useQuery } from "@tanstack/react-query";
import { LockKeyhole, Plus } from "lucide-react";
import { useState } from "react";

import { getWalletPrincipalOrganizacion, getWalletsOrganizacion, getWalletsUsuario, walletQueryKeys } from "../api";
import { CreateOrganizationWalletModal } from "../components/CreateOrganizationWalletModal";
import { WalletsList } from "../components/WalletsList";
import { WalletsSummary } from "../components/WalletsSummary";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canManageOrganizationWallets, canViewOrganizationWallets, isClient } from "../../../shared/utils/roles";

function isNotFound(error) {
  return error?.response?.status === 404;
}

export function WalletsPage() {
  const { token, user } = useAuth();
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const organizationId = user?.organizacion_id || "current";
  const hasToken = Boolean(token);
  const isClientUser = isClient(user);
  const canViewOrganization = canViewOrganizationWallets(user);
  const canManageOrganization = canManageOrganizationWallets(user);
  const hasOrganization = Boolean(user?.organizacion_id);
  const canLoadOrganizationWallets = hasToken && canViewOrganization && hasOrganization && !isClientUser;

  const userWalletsQuery = useQuery({
    queryKey: walletQueryKeys.user(organizationId),
    queryFn: () => getWalletsUsuario(),
    enabled: hasToken,
    retry: false,
  });

  const organizationWalletsQuery = useQuery({
    queryKey: walletQueryKeys.organization(organizationId),
    queryFn: () => getWalletsOrganizacion(),
    enabled: canLoadOrganizationWallets,
    retry: false,
  });

  const organizationPrincipalQuery = useQuery({
    queryKey: walletQueryKeys.organizationPrincipal(organizationId),
    queryFn: () => getWalletPrincipalOrganizacion(),
    enabled: canLoadOrganizationWallets,
    retry: false,
  });

  const principalNotFound = isNotFound(organizationPrincipalQuery.error);
  const principalWallet = principalNotFound ? null : organizationPrincipalQuery.data;
  const organizationWallets = organizationWalletsQuery.data || [];
  const userWallets = userWalletsQuery.data || [];

  if (isClientUser) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Mis wallets</h1>
          <p className="mt-1 text-sm text-slate-500">Consulta saldos y estados de tus wallets asignadas.</p>
        </div>

        <Card>
          <CardHeader title="Mis wallets" description="Wallets de usuario visibles para tu sesion." />
          <WalletsList
            wallets={userWallets}
            loading={userWalletsQuery.isLoading}
            error={userWalletsQuery.error}
            emptyTitle="Sin wallets asignadas"
            emptyDescription="Todavia no tenes wallets de usuario disponibles."
            onRetry={() => userWalletsQuery.refetch()}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Wallets</h1>
          <p className="mt-1 text-sm text-slate-500">
            Consulta saldos, estados y wallets de usuario u organizacion segun tu rol.
          </p>
        </div>
        {canManageOrganization && hasOrganization ? (
          <Button icon={Plus} onClick={() => setCreateModalOpen(true)}>
            Crear wallet de organizacion
          </Button>
        ) : null}
      </div>

      <WalletsSummary
        principalWallet={principalWallet}
        organizationWallets={organizationWallets}
        userWallets={userWallets}
        canViewOrganization={canViewOrganization}
        organizationLoading={organizationWalletsQuery.isLoading}
        principalLoading={organizationPrincipalQuery.isLoading}
        userLoading={userWalletsQuery.isLoading}
      />

      {canViewOrganization ? (
        hasOrganization ? (
          <>
            <Card>
              <CardHeader
                title="Wallet principal de organizacion"
                description="Saldo operativo principal y estado actual."
              />
              <WalletsList
                wallets={principalWallet ? [principalWallet] : []}
                loading={organizationPrincipalQuery.isLoading}
                error={principalNotFound ? null : organizationPrincipalQuery.error}
                emptyTitle="Sin wallet principal"
                emptyDescription="La organizacion todavia no tiene una wallet principal activa."
                onRetry={() => organizationPrincipalQuery.refetch()}
                featured
              />
            </Card>

            <Card>
              <CardHeader
                title="Wallets de organizacion"
                description="Wallets propias de la organizacion para caja, operacion y recompensas."
              />
              <WalletsList
                wallets={organizationWallets}
                loading={organizationWalletsQuery.isLoading}
                error={organizationWalletsQuery.error}
                emptyTitle="Sin wallets de organizacion"
                emptyDescription="Crea una wallet de organizacion para gestionar saldos operativos."
                onRetry={() => organizationWalletsQuery.refetch()}
              />
            </Card>
          </>
        ) : (
          <Card>
            <CardHeader title="Wallets de organizacion" description="Consulta y gestion disponibles por rol." />
            <ErrorState
              title="Organizacion no disponible"
              message="Tu usuario no tiene una organizacion asociada para consultar wallets de organizacion."
            />
          </Card>
        )
      ) : (
        <Card>
          <CardHeader title="Wallets de organizacion" description="Consulta y gestion disponibles por rol." />
          <EmptyState
            icon={LockKeyhole}
            title="No tenes permisos para gestionar wallets de organizacion."
            description="Tu rol actual no puede listar ni crear wallets de organizacion."
          />
        </Card>
      )}

      <Card>
        <CardHeader
          title="Mis wallets / wallets de usuario"
          description="Wallets de usuario visibles de acuerdo a tus permisos."
        />
        <WalletsList
          wallets={userWallets}
          loading={userWalletsQuery.isLoading}
          error={userWalletsQuery.error}
          emptyTitle="Sin wallets de usuario"
          emptyDescription="No hay wallets de usuario visibles para tu sesion."
          onRetry={() => userWalletsQuery.refetch()}
        />
      </Card>

      <CreateOrganizationWalletModal open={createModalOpen} onClose={() => setCreateModalOpen(false)} />
    </div>
  );
}
