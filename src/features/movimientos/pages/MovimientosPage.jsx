import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getMovimientos, movementQueryKeys } from "../api";
import { CreateMovementModal } from "../components/CreateMovementModal";
import { MovementDetailModal } from "../components/MovementDetailModal";
import { MovementsTable } from "../components/MovementsTable";
import { MovementsToolbar } from "../components/MovementsToolbar";
import { ReverseMovementModal } from "../components/ReverseMovementModal";
import { createWalletMap, getMovementKind } from "../movementUtils";
import { getWalletsOrganizacion, getWalletsUsuario, walletQueryKeys } from "../../wallets/api";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import {
  canCreateClientPayment,
  canCreateFinancialMovement,
  canReverseMovement,
  canViewMovements,
  canViewOrganizationWallets,
} from "../../../shared/utils/roles";

const initialFilters = {
  tipo: "",
  estado: "",
  search: "",
};

const emptyArray = [];

function filterMovements(movements, filters) {
  const search = filters.search.trim().toLowerCase();

  return movements.filter((movement) => {
    const typeMatches = !filters.tipo || getMovementKind(movement) === filters.tipo;
    const statusMatches = !filters.estado || movement.estado === filters.estado;
    const searchTarget = [
      movement.descripcion,
      movement.referencia_externa,
      movement.id,
      movement.wallet_origen_id,
      movement.wallet_destino_id,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchMatches = !search || searchTarget.includes(search);
    return typeMatches && statusMatches && searchMatches;
  });
}

export function MovimientosPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState(initialFilters);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedMovement, setSelectedMovement] = useState(null);
  const [movementToReverse, setMovementToReverse] = useState(null);

  const organizationId = user?.organizacion_id || "current";
  const hasToken = Boolean(token);
  const hasOrganization = Boolean(user?.organizacion_id);
  const canView = canViewMovements(user);
  const canCreate = canCreateFinancialMovement(user) || canCreateClientPayment(user);
  const canViewOrganizationWalletsForRole = canViewOrganizationWallets(user);

  const movementsQuery = useQuery({
    queryKey: movementQueryKeys.list(organizationId),
    queryFn: () => getMovimientos({ skip: 0, limit: 100 }),
    enabled: hasToken && canView,
    retry: false,
  });

  const userWalletsQuery = useQuery({
    queryKey: walletQueryKeys.user(organizationId),
    queryFn: () => getWalletsUsuario(),
    enabled: hasToken,
    retry: false,
  });

  const organizationWalletsQuery = useQuery({
    queryKey: walletQueryKeys.organization(organizationId),
    queryFn: () => getWalletsOrganizacion(),
    enabled: hasToken && hasOrganization && canViewOrganizationWalletsForRole,
    retry: false,
  });

  const movements = movementsQuery.data || emptyArray;
  const userWallets = userWalletsQuery.data || emptyArray;
  const organizationWallets = organizationWalletsQuery.data || emptyArray;
  const allWallets = useMemo(
    () => Array.from(createWalletMap([...userWallets, ...organizationWallets]).values()),
    [organizationWallets, userWallets],
  );
  const walletMap = useMemo(() => createWalletMap(allWallets), [allWallets]);
  const filteredMovements = useMemo(() => filterMovements(movements, filters), [filters, movements]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Movimientos</h1>
        <p className="mt-1 text-sm text-slate-500">
          Seguimiento y creacion de operaciones sobre wallets de usuario y organizacion.
        </p>
      </div>

      <MovementsToolbar
        filters={filters}
        onChange={setFilters}
        onCreate={() => setCreateModalOpen(true)}
        canCreate={canCreate}
      />

      <Card>
        <CardHeader title="Actividad reciente" description="Ultimos movimientos visibles para tu sesion." />
        {canView ? (
          <MovementsTable
            movements={filteredMovements}
            walletMap={walletMap}
            loading={movementsQuery.isLoading}
            error={movementsQuery.error}
            onRetry={() => movementsQuery.refetch()}
            onView={setSelectedMovement}
            onReverse={setMovementToReverse}
            canReverse={canReverseMovement(user)}
          />
        ) : (
          <EmptyState title="Sin permisos" description="No tenes permisos para consultar movimientos." />
        )}
      </Card>

      <CreateMovementModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        user={user}
        allWallets={allWallets}
        userWallets={userWallets}
        organizationWallets={organizationWallets}
      />
      <MovementDetailModal movement={selectedMovement} walletMap={walletMap} onClose={() => setSelectedMovement(null)} />
      <ReverseMovementModal movement={movementToReverse} onClose={() => setMovementToReverse(null)} />
    </div>
  );
}
