import { ShieldCheck, ToggleLeft } from "lucide-react";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Button } from "../../../shared/components/ui/Button";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { formatDateTime } from "../../../shared/utils/formatters";
import { canChangeUserRole, canChangeUserStatus } from "../../../shared/utils/roles";
import { getUsuarioCreatedAt } from "../schemas";
import { UserRoleBadge } from "./UserRoleBadge";
import { UserStatusBadge } from "./UserStatusBadge";

function LoadingRows({ columnsCount }) {
  return (
    <tbody className="divide-y divide-slate-100 bg-white">
      {Array.from({ length: 4 }).map((_, index) => (
        <tr key={index}>
          {Array.from({ length: columnsCount }).map((__, cellIndex) => (
            <td key={cellIndex} className="px-4 py-3">
              <div className="h-4 w-full max-w-32 animate-pulse rounded bg-slate-100" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}

function ActionsCell({ usuario, currentUser, onChangeRole, onChangeStatus }) {
  const canEditRole = canChangeUserRole(currentUser, usuario);
  const canEditStatus = canChangeUserStatus(currentUser, usuario);

  if (!canEditRole && !canEditStatus) {
    return <span className="text-xs text-slate-400">Sin acciones</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {canEditRole ? (
        <Button variant="secondary" size="sm" icon={ShieldCheck} onClick={() => onChangeRole(usuario)}>
          Rol
        </Button>
      ) : null}
      {canEditStatus ? (
        <Button variant="secondary" size="sm" icon={ToggleLeft} onClick={() => onChangeStatus(usuario)}>
          Estado
        </Button>
      ) : null}
    </div>
  );
}

export function UsersTable({ usuarios, currentUser, loading, error, onRetry, onChangeRole, onChangeStatus }) {
  const hasCreatedAt = usuarios.some((usuario) => Boolean(getUsuarioCreatedAt(usuario)));
  const columnsCount = hasCreatedAt ? 6 : 5;

  if (error) {
    return (
      <ErrorState
        title="No se pudieron cargar los usuarios"
        message={getApiErrorMessage(error)}
        onRetry={onRetry}
      />
    );
  }

  if (!loading && !usuarios.length) {
    return (
      <EmptyState
        title="Sin usuarios"
        description="No hay usuarios para mostrar con los filtros actuales."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                Nombre
              </th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                Email
              </th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                Rol
              </th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                Estado
              </th>
              {hasCreatedAt ? (
                <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                  Creacion
                </th>
              ) : null}
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                Acciones
              </th>
            </tr>
          </thead>
          {loading ? (
            <LoadingRows columnsCount={columnsCount} />
          ) : (
            <tbody className="divide-y divide-slate-100 bg-white">
              {usuarios.map((usuario) => (
                <tr key={usuario.id}>
                  <td className="px-4 py-3 text-slate-900">
                    <span className="font-medium">{usuario.nombre}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{usuario.email}</td>
                  <td className="px-4 py-3">
                    <UserRoleBadge rol={usuario.rol} />
                  </td>
                  <td className="px-4 py-3">
                    <UserStatusBadge usuario={usuario} />
                  </td>
                  {hasCreatedAt ? (
                    <td className="px-4 py-3 text-slate-600">{formatDateTime(getUsuarioCreatedAt(usuario))}</td>
                  ) : null}
                  <td className="px-4 py-3">
                    <ActionsCell
                      usuario={usuario}
                      currentUser={currentUser}
                      onChangeRole={onChangeRole}
                      onChangeStatus={onChangeStatus}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
