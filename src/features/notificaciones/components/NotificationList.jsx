import { getApiErrorMessage } from "../../../shared/api/apiError";
import { ErrorState } from "../../../shared/components/feedback/ErrorState";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { NotificationCard } from "./NotificationCard";

function NotificationSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex gap-2">
        <div className="h-7 w-24 animate-pulse rounded-full bg-slate-100" />
        <div className="h-7 w-20 animate-pulse rounded-full bg-slate-100" />
      </div>
      <div className="mt-4 h-5 w-64 max-w-full animate-pulse rounded bg-slate-100" />
      <div className="mt-3 h-4 w-full animate-pulse rounded bg-slate-100" />
      <div className="mt-2 h-4 w-2/3 animate-pulse rounded bg-slate-100" />
    </div>
  );
}

export function NotificationList({
  notifications = [],
  loading = false,
  error,
  onRetry,
  onView,
  onMarkRead,
  markingId,
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((item) => (
          <NotificationSkeleton key={item} />
        ))}
      </div>
    );
  }

  if (error) {
    return <ErrorState message={getApiErrorMessage(error)} onRetry={onRetry} />;
  }

  if (!notifications.length) {
    return <EmptyState title="No tenes notificaciones todavia." description="Los eventos relevantes de wallets, movimientos y seguridad apareceran aca." />;
  }

  return (
    <div className="space-y-3">
      {notifications.map((notification) => (
        <NotificationCard
          key={notification.id}
          notification={notification}
          onView={onView}
          onMarkRead={onMarkRead}
          markingRead={markingId === notification.id}
        />
      ))}
    </div>
  );
}
