import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Inbox } from "lucide-react";
import { useMemo, useState } from "react";

import {
  getNotificaciones,
  getNotificacionesOrganizacion,
  getUnreadNotificationsCount,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  notificationQueryKeys,
} from "../api";
import { NotificationDetailModal } from "../components/NotificationDetailModal";
import { NotificationList } from "../components/NotificationList";
import { NotificationsToolbar } from "../components/NotificationsToolbar";
import { normalizeNotificationList } from "../notificationUtils";
import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { useAuth } from "../../../shared/hooks/useAuth";
import { formatNumber } from "../../../shared/utils/formatters";
import { canViewOrganizationNotifications } from "../../../shared/utils/roles";

const initialFilters = {
  readStatus: "",
  tipo: "",
  canal: "",
  search: "",
};

const emptyNotificationList = {
  items: [],
  total: 0,
  noLeidas: 0,
};

function filterNotifications(notifications, filters) {
  const search = filters.search.trim().toLowerCase();

  return notifications.filter((notification) => {
    const readMatches =
      !filters.readStatus ||
      (filters.readStatus === "read" && notification.leida) ||
      (filters.readStatus === "unread" && !notification.leida);
    const typeMatches = !filters.tipo || notification.tipo === filters.tipo;
    const channelMatches = !filters.canal || notification.canal === filters.canal;
    const searchTarget = [
      notification.titulo,
      notification.mensaje,
      notification.id,
      notification.error_envio,
      notification.metadata ? JSON.stringify(notification.metadata) : "",
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchMatches = !search || searchTarget.includes(search);
    return readMatches && typeMatches && channelMatches && searchMatches;
  });
}

function SummaryCard({ title, value, description, icon: Icon, loading = false }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          {loading ? (
            <div className="mt-3 h-7 w-20 animate-pulse rounded bg-slate-100" />
          ) : (
            <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-brand-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

export function NotificacionesPage() {
  const { token, user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [filters, setFilters] = useState(initialFilters);
  const [scope, setScope] = useState("me");
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [actionError, setActionError] = useState(null);

  const hasToken = Boolean(token);
  const organizationId = user?.organizacion_id || "current";
  const canViewOrganization = canViewOrganizationNotifications(user);
  const activeScope = canViewOrganization ? scope : "me";

  const personalNotificationsQuery = useQuery({
    queryKey: notificationQueryKeys.list("me"),
    queryFn: () => getNotificaciones({ skip: 0, limit: 100 }),
    enabled: hasToken,
    retry: false,
    select: normalizeNotificationList,
  });

  const organizationNotificationsQuery = useQuery({
    queryKey: notificationQueryKeys.organization(organizationId),
    queryFn: () => getNotificacionesOrganizacion({ skip: 0, limit: 200 }),
    enabled: hasToken && canViewOrganization && activeScope === "organization",
    retry: false,
    select: normalizeNotificationList,
  });

  const unreadCountQuery = useQuery({
    queryKey: notificationQueryKeys.unreadCount,
    queryFn: getUnreadNotificationsCount,
    enabled: hasToken,
    retry: false,
  });

  const activeQuery = activeScope === "organization" ? organizationNotificationsQuery : personalNotificationsQuery;
  const notificationList = activeQuery.data || emptyNotificationList;
  const filteredNotifications = useMemo(
    () => filterNotifications(notificationList.items, filters),
    [filters, notificationList.items],
  );
  const unreadCount = unreadCountQuery.data ?? notificationList.noLeidas;

  const invalidateNotifications = () => {
    queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const markReadMutation = useMutation({
    mutationFn: markNotificationAsRead,
    onSuccess: (notification) => {
      setActionError(null);
      invalidateNotifications();
      if (selectedNotification?.id === notification.id) {
        setSelectedNotification(notification);
      }
      showToast({
        title: "Notificacion actualizada",
        message: "La notificacion fue marcada como leida.",
      });
    },
    onError: (error) => {
      setActionError(getApiErrorMessage(error));
    },
  });

  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsAsRead,
    onSuccess: (count) => {
      setActionError(null);
      invalidateNotifications();
      showToast({
        title: "Notificaciones actualizadas",
        message: `${formatNumber(count)} notificaciones marcadas como leidas.`,
      });
    },
    onError: (error) => {
      setActionError(getApiErrorMessage(error));
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Notificaciones</h1>
        <p className="mt-1 text-sm text-slate-500">Centro de eventos internos, emails y estados de lectura.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard
          title="No leidas"
          value={formatNumber(unreadCount)}
          description="Pendientes en tu bandeja visible"
          icon={BellRing}
          loading={unreadCountQuery.isLoading}
        />
        <SummaryCard
          title="Total visible"
          value={formatNumber(notificationList.total)}
          description={activeScope === "organization" ? "Bandeja de organizacion" : "Bandeja personal"}
          icon={Inbox}
          loading={activeQuery.isLoading}
        />
      </div>

      <NotificationsToolbar
        filters={filters}
        onChange={setFilters}
        scope={activeScope}
        onScopeChange={setScope}
        canViewOrganization={canViewOrganization}
        onMarkAllRead={() => markAllMutation.mutate()}
        markingAll={markAllMutation.isPending}
        unreadCount={unreadCount}
      />

      {actionError ? <ErrorState title="No se pudo actualizar" message={actionError} /> : null}

      <Card>
        <CardHeader
          title={activeScope === "organization" ? "Notificaciones de organizacion" : "Mis notificaciones"}
          description="Eventos ordenados por fecha, con acciones de lectura y detalle."
        />
        <NotificationList
          notifications={filteredNotifications}
          loading={activeQuery.isLoading}
          error={activeQuery.error}
          onRetry={() => activeQuery.refetch()}
          onView={setSelectedNotification}
          onMarkRead={(notification) => markReadMutation.mutate(notification.id)}
          markingId={markReadMutation.isPending ? markReadMutation.variables : null}
        />
      </Card>

      <NotificationDetailModal notification={selectedNotification} onClose={() => setSelectedNotification(null)} />
    </div>
  );
}
