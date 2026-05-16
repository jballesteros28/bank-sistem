import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { UserRoundCog } from "lucide-react";

import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canCreateUsers, canViewUsers } from "../../../shared/utils/roles";
import { getUsuarios, usuariosQueryKeys } from "../api";
import { ChangeRoleModal } from "../components/ChangeRoleModal";
import { ChangeStatusModal } from "../components/ChangeStatusModal";
import { CreateUserModal } from "../components/CreateUserModal";
import { UsersTable } from "../components/UsersTable";
import { UsersToolbar } from "../components/UsersToolbar";
import { getUsuarioStatus } from "../schemas";

const initialFilters = {
  rol: "",
  estado: "",
  search: "",
};

const emptyArray = [];

function filterUsuarios(usuarios, filters) {
  const search = filters.search.trim().toLowerCase();

  return usuarios.filter((usuario) => {
    const roleMatches = !filters.rol || usuario.rol === filters.rol;
    const statusMatches = !filters.estado || getUsuarioStatus(usuario) === filters.estado;
    const searchTarget = [usuario.nombre, usuario.email, usuario.id].filter(Boolean).join(" ").toLowerCase();
    const searchMatches = !search || searchTarget.includes(search);
    return roleMatches && statusMatches && searchMatches;
  });
}

export function UsuariosPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState(initialFilters);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [roleTarget, setRoleTarget] = useState(null);
  const [statusTarget, setStatusTarget] = useState(null);

  const organizationId = user?.organizacion_id || "global";
  const canView = canViewUsers(user);
  const canCreate = canCreateUsers(user);

  const usuariosQuery = useQuery({
    queryKey: usuariosQueryKeys.list(organizationId),
    queryFn: () => getUsuarios(),
    enabled: Boolean(token) && canView,
    retry: false,
  });

  const usuarios = usuariosQuery.data || emptyArray;
  const filteredUsuarios = useMemo(() => filterUsuarios(usuarios, filters), [filters, usuarios]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Usuarios</h1>
        <p className="mt-1 text-sm text-slate-500">
          Administra altas, roles y activacion de usuarios dentro de la organizacion.
        </p>
      </div>

      {canView ? (
        <UsersToolbar
          filters={filters}
          onChange={setFilters}
          onCreate={() => setCreateModalOpen(true)}
          canCreate={canCreate}
        />
      ) : null}

      <Card>
        <CardHeader title="Usuarios de la organizacion" description="Listado real segun los permisos del backend." />
        {canView ? (
          <UsersTable
            usuarios={filteredUsuarios}
            currentUser={user}
            loading={usuariosQuery.isLoading}
            error={usuariosQuery.error}
            onRetry={() => usuariosQuery.refetch()}
            onChangeRole={setRoleTarget}
            onChangeStatus={setStatusTarget}
          />
        ) : (
          <EmptyState
            icon={UserRoundCog}
            title="Sin permisos"
            description="Tu rol no tiene acceso a la administracion de usuarios."
          />
        )}
      </Card>

      <CreateUserModal open={createModalOpen} onClose={() => setCreateModalOpen(false)} />
      <ChangeRoleModal usuario={roleTarget} currentUser={user} onClose={() => setRoleTarget(null)} />
      <ChangeStatusModal usuario={statusTarget} currentUser={user} onClose={() => setStatusTarget(null)} />
    </div>
  );
}
