import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const notificationQueryKeys = {
  all: ["notificaciones"],
  list: (scope = "me") => ["notificaciones", "list", scope],
  organization: (organizationId = "current") => ["notificaciones", "organization", organizationId || "current"],
  unreadCount: ["notificaciones", "unread-count"],
};

export function listNotificaciones(params) {
  return httpClient.get(endpoints.notificaciones.list, { params });
}

export function getNotificaciones(params) {
  return listNotificaciones(params);
}

export function getNotificacionesOrganizacion(params) {
  return httpClient.get(endpoints.notificaciones.organization, { params });
}

export function getUnreadNotificationsCount() {
  return httpClient.get(endpoints.notificaciones.unreadCount);
}

export function markNotificationAsRead(id) {
  return httpClient.patch(endpoints.notificaciones.markRead(id), { leida: true });
}

export function markAllNotificationsAsRead() {
  return httpClient.patch(endpoints.notificaciones.markAllRead);
}
